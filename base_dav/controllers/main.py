# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import hashlib
import hmac
import io
import logging
import re
import secrets
import time
from configparser import RawConfigParser as ConfigParser
from urllib.parse import urlparse

import werkzeug
from odoo import http
from odoo.http import request

try:
    import radicale
except ImportError:
    radicale = None

PREFIX = "/.dav"
DIGEST_REALM = "Odoo CardDAV"
NONCE_TTL_SECONDS = 300
_LOGGER = logging.getLogger(__name__)


def _parse_digest_header(value):
    if not value or not value.startswith("Digest "):
        return {}
    value = value[len("Digest ") :]
    result = {}
    for key, _quoted, qvalue, uvalue in re.findall(
        r'(\\w+)=("([^"]*)"|([^,]*))', value
    ):
        result[key] = qvalue or uvalue.strip()
    return result


def _get_digest_secret():
    icp = request.env["ir.config_parameter"].sudo()
    secret = icp.get_param("base_dav.digest_secret")
    if not secret:
        secret = secrets.token_urlsafe(32)
        icp.set_param("base_dav.digest_secret", secret)
    return secret


def _normalize_digest_value(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


def _build_nonce(secret):
    timestamp = str(int(time.time()))
    signature = hmac.new(
        secret.encode(),
        timestamp.encode(),
        hashlib.sha256,
    ).hexdigest()
    payload = f"{timestamp}:{signature}".encode()
    return base64.b64encode(payload).decode()


def _validate_nonce(nonce, secret):
    try:
        raw = base64.b64decode(nonce.encode()).decode()
        timestamp, signature = raw.split(":", 1)
        expected = hmac.new(
            secret.encode(),
            timestamp.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False, False
        if time.time() - int(timestamp) > NONCE_TTL_SECONDS:
            return False, True
        return True, False
    except Exception:
        return False, False


def _digest_challenge(stale=False):
    secret = _get_digest_secret()
    nonce = _build_nonce(secret)
    opaque = hashlib.md5(secret.encode()).hexdigest()
    header = (
        f'Digest realm="{DIGEST_REALM}", '
        f'nonce="{nonce}", algorithm=MD5, qop="auth", opaque="{opaque}"'
    )
    if stale:
        header += ", stale=true"
    return http.Response(
        status=401,
        headers=[("WWW-Authenticate", header)],
    )


def _ha2(method, uri, qop, body):
    if qop == "auth-int":
        body_hash = hashlib.md5(body or b"").hexdigest()
        data = f"{method}:{uri}:{body_hash}"
    else:
        data = f"{method}:{uri}"
    return hashlib.md5(data.encode()).hexdigest()


def _ha1(username, realm, token):
    if isinstance(token, bytes):
        data = (
            username.encode()
            + b":" + realm.encode()
            + b":" + token
        )
    else:
        data = f"{username}:{realm}:{token}".encode()
    return hashlib.md5(data).hexdigest()


def _digest_response(username, realm, token, method, uri, nonce, nc, cnonce,
                     qop, body):
    ha1 = _ha1(username, realm, token)
    ha2 = _ha2(method, uri, qop, body)
    if qop:
        return hashlib.md5(
            f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode()
        ).hexdigest()
    return hashlib.md5(
        f"{ha1}:{nonce}:{ha2}".encode()
    ).hexdigest()


def _digest_response_sess(username, realm, token, method, uri, nonce, cnonce,
                          qop, nc, body):
    ha1 = _ha1(username, realm, token)
    ha1 = hashlib.md5(
        f"{ha1}:{nonce}:{cnonce}".encode()
    ).hexdigest()
    ha2 = _ha2(method, uri, qop, body)
    if qop:
        return hashlib.md5(
            f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode()
        ).hexdigest()
    return hashlib.md5(
        f"{ha1}:{nonce}:{ha2}".encode()
    ).hexdigest()


def _find_user_by_login(login):
    if not login:
        return request.env["res.users"]
    users = request.env["res.users"].sudo().search(
        [("login", "=", login)], limit=1
    )
    if users:
        return users
    return request.env["res.users"].sudo().search(
        [("email", "=", login)], limit=1
    )


def _authenticate_digest(method, path, body=None):  # noqa: C901
    auth_header = request.httprequest.headers.get("Authorization")
    if not auth_header:
        environ = request.httprequest.environ
        auth_header = (
            environ.get("HTTP_AUTHORIZATION")
            or environ.get("Authorization")
            or environ.get("REDIRECT_HTTP_AUTHORIZATION")
        )
    digest = _parse_digest_header(auth_header)
    if not digest:
        auth = getattr(request.httprequest, "authorization", None)
        if auth and getattr(auth, "type", "").lower() == "digest":
            params = dict(getattr(auth, "parameters", {}) or {})
            for key in (
                "username",
                "realm",
                "nonce",
                "uri",
                "response",
                "opaque",
                "algorithm",
                "qop",
                "nc",
                "cnonce",
            ):
                value = getattr(auth, key, None)
                if value is not None and key not in params:
                    params[key] = value
            digest = {k: _normalize_digest_value(v) for k, v in params.items()}
        if digest:
            _LOGGER.info(
                "CardDAV Digest: parsed from request.authorization for %s (keys=%s)",
                path,
                sorted(digest.keys()),
            )

    if not digest:
        header_names = [
            key for key in request.httprequest.headers.keys()
        ]
        _LOGGER.info(
            "CardDAV Digest: no Authorization header for %s (headers=%s)",
            path,
            header_names,
        )
        return False, _digest_challenge()
    _LOGGER.info(
        (
            "CardDAV Digest: auth header present for %s "
            "(user=%s realm=%s uri=%s algo=%s qop=%s)"
        ),
        path,
        digest.get("username"),
        digest.get("realm"),
        digest.get("uri"),
        (digest.get("algorithm") or "MD5"),
        digest.get("qop"),
    )

    if digest.get("realm") != DIGEST_REALM:
        _LOGGER.info(
            "CardDAV Digest: realm mismatch for %s (got %s)",
            path,
            digest.get("realm"),
        )
        return False, _digest_challenge()

    secret = _get_digest_secret()
    nonce = digest.get("nonce")
    valid, stale = _validate_nonce(nonce or "", secret)
    if not valid:
        _LOGGER.info(
            "CardDAV Digest: invalid nonce for %s (stale=%s)",
            path,
            stale,
        )
        return False, _digest_challenge(stale=stale)

    username = digest.get("username")
    if not username:
        _LOGGER.info("CardDAV Digest: missing username for %s", path)
        return False, _digest_challenge()

    user = _find_user_by_login(username)
    token = (user.carddav_token or "").strip() if user else ""
    if not user or not token:
        _LOGGER.info(
            "CardDAV Digest: unknown user or missing token for %s (%s)",
            path,
            username,
        )
        return False, _digest_challenge()

    token_candidates = [token]
    b64_variant = token.replace("-", "+").replace("_", "/")
    if b64_variant != token:
        token_candidates.append(b64_variant)
    for candidate in list(token_candidates):
        try:
            padded = candidate + ("=" * (-len(candidate) % 4))
            decoded = base64.b64decode(padded)
            if decoded:
                token_candidates.append(decoded)
        except Exception:  # pragma: no cover
            _LOGGER.debug(
                "CardDAV Digest: failed to decode token candidate for %s",
                path,
                exc_info=True,
            )
            continue
    # de-dupe while preserving order
    seen_token = set()
    deduped = []
    for t in token_candidates:
        key = t if isinstance(t, str) else t.hex()
        if key in seen_token:
            continue
        seen_token.add(key)
        deduped.append(t)
    token_candidates = deduped

    uri = digest.get("uri") or path
    qop = (digest.get("qop") or "").split(",")[0].strip()
    nc = digest.get("nc", "")
    if isinstance(nc, int):
        nc = f"{nc:08x}"
    cnonce = digest.get("cnonce", "")
    nonce_candidates = [nonce]
    if isinstance(nonce, str) and ":" in nonce:
        try:
            encoded = base64.b64encode(nonce.encode()).decode()
            nonce_candidates.append(encoded)
        except Exception:  # pragma: no cover
            _LOGGER.debug(
                "CardDAV Digest: failed to encode nonce candidate for %s",
                path,
                exc_info=True,
            )
    if qop and (not nc or not cnonce):
        # Some clients send qop without nc/cnonce; fall back to RFC 2069.
        qop = ""
    algorithm = (digest.get("algorithm") or "MD5").upper()
    uris = [uri]
    parsed = urlparse(uri)
    if parsed.scheme and parsed.netloc:
        normalized = parsed.path or ""
        if parsed.query:
            normalized = f"{normalized}?{parsed.query}"
        uris.append(normalized)
    if uri.endswith("/") and uri != "/":
        uris.append(uri.rstrip("/"))
    else:
        uris.append(f"{uri}/")
    uris.append(uri.lstrip("/"))
    try:
        from urllib.parse import unquote

        uris.append(unquote(uri))
    except Exception:  # pragma: no cover
        _LOGGER.debug(
            "CardDAV Digest: failed to unquote URI candidate for %s",
            path,
            exc_info=True,
        )
    # de-dupe while preserving order
    seen = set()
    uris = [u for u in uris if not (u in seen or seen.add(u))]

    expected_values = []
    qop_candidates = [qop]
    if qop:
        # Accept RFC 2069-style response even if qop is provided.
        qop_candidates.append("")
    if body is not None:
        qop_candidates.append("auth-int")
    # de-dupe while preserving order
    seen_qop = set()
    qop_candidates = [
        q for q in qop_candidates if not (q in seen_qop or seen_qop.add(q))
    ]
    methods = [method, method.upper(), method.lower()]
    algorithms = [algorithm, "MD5", "MD5-SESS"]
    seen_alg = set()
    algorithms = [a for a in algorithms if not (a in seen_alg or seen_alg.add(a))]
    for candidate_uri in uris:
        for candidate_nonce in nonce_candidates:
            for candidate_method in methods:
                for candidate_qop in qop_candidates:
                    for candidate_alg in algorithms:
                        for candidate_token in token_candidates:
                            if candidate_alg == "MD5-SESS":
                                expected_values.append(
                                    _digest_response_sess(
                                        username=username,
                                        realm=DIGEST_REALM,
                                        token=candidate_token,
                                        method=candidate_method,
                                        uri=candidate_uri,
                                        nonce=candidate_nonce,
                                        nc=nc,
                                        cnonce=cnonce,
                                        qop=candidate_qop,
                                        body=body,
                                    )
                                )
                            else:
                                expected_values.append(
                                    _digest_response(
                                        username=username,
                                        realm=DIGEST_REALM,
                                        token=candidate_token,
                                        method=candidate_method,
                                        uri=candidate_uri,
                                        nonce=candidate_nonce,
                                        nc=nc,
                                        cnonce=cnonce,
                                        qop=candidate_qop,
                                        body=body,
                                    )
                                )

    response = digest.get("response", "")
    if not any(hmac.compare_digest(response, value) for value in expected_values):
        _LOGGER.info(
            "CardDAV Digest: response mismatch for %s (%s, algo=%s, uri=%s)",
            path,
            username,
            algorithm,
            uri,
        )
        _LOGGER.info(
            "CardDAV Digest: expected=%s got=%s qop=%s nc=%s cnonce=%s",
            expected_values[0] if expected_values else "",
            response,
            qop,
            nc,
            cnonce,
        )
        return False, _digest_challenge()

    _LOGGER.info("CardDAV Digest: authenticated user %s for %s", username, path)
    return True, user


class Main(http.Controller):
    @http.route(
        ['/.well-known/carddav', '/.well-known/caldav', '/.well-known/webdav'],
        type='http', auth='none', csrf=False,
    )
    def handle_well_known_request(self):
        return werkzeug.utils.redirect(PREFIX, 301)

    @http.route(
        [PREFIX, '%s/<path:davpath>' % PREFIX], type='http', auth='none',
        csrf=False,
    )
    def handle_dav_request(self, davpath=None):
        body = request.httprequest.get_data() or b""
        ok, result = _authenticate_digest(
            request.httprequest.method, request.httprequest.path, body
        )
        if not ok:
            return result
        user = result
        if not user:
            return _digest_challenge()
        if hasattr(request, "update_env"):
            request.update_env(user=user.id)
        else:
            request._env = request.env(user=user.id)

        config = ConfigParser()
        for section, values in radicale.config.INITIAL_CONFIG.items():
            config.add_section(section)
            for key, data in values.items():
                config.set(section, key, data["value"])
        config.set('auth', 'type', 'remote_user')
        config.set(
            'storage', 'type', 'odoo.addons.base_dav.radicale.collection'
        )
        config.set(
            'rights', 'type', 'odoo.addons.base_dav.radicale.rights'
        )
        config.set('web', 'type', 'none')
        application = radicale.Application(
            config, logging.getLogger('radicale'),
        )

        status = None
        headers = None

        def start_response(response_status, response_headers):
            nonlocal status, headers
            status = response_status
            headers = response_headers

        environ = dict(
            request.httprequest.environ,
            HTTP_X_SCRIPT_NAME=PREFIX,
            PATH_INFO=davpath or '',
            REMOTE_USER=user.login,
        )
        environ["wsgi.input"] = io.BytesIO(body)
        environ["CONTENT_LENGTH"] = str(len(body))

        result = application(environ, start_response)
        return http.Response(response=result, status=status, headers=headers)
