# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""HTTP Basic authentication for DAV requests.

Every DAV route is declared ``auth="none"`` so that PROPFIND/REPORT/PUT reach
the controller at all -- Odoo's session layer only understands GET and POST.
Credentials are therefore verified here and the request environment is rebound
to the authenticated user.

The calling convention of ``res.users._login`` has changed twice since 17.0:

===========  ==================================================
17.0         ``_login(db, login, password, user_agent_env)``
18.0         ``_login(db, credential, user_agent_env)``
19.0 / 20.0  ``_login(credential, user_agent_env)`` (no db, and
             it runs on the request environment)
===========  ==================================================

17.0 returns a user id, later versions return an ``auth_info`` mapping.
"""

import base64
import logging

import odoo
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)

REALM = "Odoo DAV"


class Unauthorized(Exception):
    """Credentials are missing, wrong, or the account cannot use DAV."""


def authenticate():
    """Authenticate the request and rebind ``request.env`` to that user.

    Raises :class:`Unauthorized` when the request must be answered with 401.
    """
    login, password = _credentials()
    if not login or not password:
        raise Unauthorized("no Basic credentials supplied")

    auth_info = _login(login, password, _user_agent_env())
    if not auth_info:
        raise Unauthorized("invalid credentials")

    uid = _uid_of(auth_info)
    if not uid:
        raise Unauthorized("invalid credentials")

    user = request.env(user=uid)["res.users"].browse(uid)
    reason = _second_factor_reason(user, auth_info)
    if reason:
        _logger.warning("dav_server: refusing DAV login for %s: %s", login, reason)
        raise Unauthorized(reason)

    request.update_env(user=uid)
    return user


def _credentials():
    header = request.httprequest.headers.get("Authorization", "")
    if not header.lower().startswith("basic "):
        return None, None
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
    except Exception:
        _logger.debug("dav_server: undecodable Authorization header")
        return None, None
    login, _, password = decoded.partition(":")
    return login, password


def _user_agent_env():
    """Return the wsgienv ``_login`` expects, mirroring ``Request._authenticate``.

    Odoo's own login builds a small dict rather than passing the live WSGI
    environ through:

        {'interactive': True, 'base_location': ..., 'HTTP_HOST': ...,
         'REMOTE_ADDR': ...}

    Passing the raw environ instead breaks on a site with ``auth_oauth``
    installed. ``auth_oauth`` overrides ``_check_credentials`` and reads
    ``env['interactive']`` while handling the AccessDenied raised for a wrong
    password; a bare WSGI environ has no such key, so it raises KeyError and
    the client gets a 500 instead of the 401 the protocol requires.
    """
    return {
        "interactive": True,
        "base_location": request.httprequest.url_root.rstrip("/"),
        "HTTP_HOST": request.httprequest.environ.get("HTTP_HOST", ""),
        "REMOTE_ADDR": request.httprequest.environ.get("REMOTE_ADDR", ""),
    }


def _login(login, password, user_agent_env):
    """Call whichever ``_login`` signature this Odoo version provides.

    ``res.users._login`` *raises* ``AccessDenied`` on bad credentials rather
    than returning a falsy value. Letting it escape turns Odoo's generic
    exception handling into a 403 Forbidden, when the protocol requires a 401
    with a ``WWW-Authenticate`` challenge so the client retries.
    """
    try:
        return _call_login(login, password, user_agent_env)
    except (AccessDenied, AccessError):
        _logger.info("dav_server: rejected credentials for %r", login)
        return None


def _call_login(login, password, user_agent_env):
    users = request.env["res.users"]
    version = odoo.release.version_info
    if version >= (18, 0):
        credential = {"login": login, "password": password, "type": "password"}
        if version >= (19, 0):
            return users._login(credential, user_agent_env=user_agent_env)
        return users._login(request.db, credential, user_agent_env=user_agent_env)
    return users._login(request.db, login, password, user_agent_env=user_agent_env)


def _uid_of(auth_info):
    if isinstance(auth_info, dict):
        return auth_info.get("uid")
    return auth_info


def _second_factor_reason(user, auth_info):
    """Return why this account cannot authenticate over DAV, or None.

    CalDAV and CardDAV clients only speak HTTP Basic, so there is nowhere to
    ask for a one-time code. Rather than let the account silently fail on every
    sync, it is refused up front with an explicit reason.
    """
    if isinstance(auth_info, dict):
        marker = auth_info.get("mfa")
        if marker not in (None, "skip"):
            return "the account requires a second authentication factor"
    if user.totp_secret:
        return "the account has two-factor authentication enabled"
    mfa_url = getattr(user, "_mfa_url", None)
    if callable(mfa_url) and mfa_url():
        return "the account requires a second authentication factor"
    return None
