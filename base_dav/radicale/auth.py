# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from radicale.auth import BaseAuth

from odoo.http import request

_logger = logging.getLogger(__name__)


def load(configuration):
    """Create Radicale authentication backend instance.

    This function is used by Radicale to initialize the authentication
    plugin for the current configuration.

    :param configuration: Radicale configuration object
    :type configuration: Any

    :return: Auth backend instance
    :rtype: Auth
    """
    return Auth(configuration)


def _user_agent_env(ctx):
    """Build user_agent_env dictionary for Odoo ``res.users._login``.

    Extracts:
      - HTTP_USER_AGENT
      - REMOTE_ADDR

    from Radicale request context.

    :param ctx: Radicale request context
    :type ctx: Any

    :return: Environment dictionary for login
    :rtype: Dict[str, str]
    """
    env = {"interactive": False}

    user_agent = getattr(ctx, "user_agent", None)
    if user_agent:
        env["HTTP_USER_AGENT"] = str(user_agent)

    remote = (
        getattr(ctx, "remote_host", None)
        or getattr(ctx, "remote_addr", None)
        or getattr(ctx, "client", None)
    )
    if remote:
        if isinstance(remote, (tuple | list)):
            remote = remote[0] if remote else None
        if remote:
            env["REMOTE_ADDR"] = str(remote)

    return env


def _set_request_user(base_env, uid):
    """Switch current Odoo HTTP request to authenticated user.

    Updates:
      - request.uid
      - request.env (via update_env or manual environment rebuild)

    :param base_env: Original Odoo environment
    :type base_env: odoo.models.BaseModel
    :param uid: Authenticated user ID
    :type uid: int
    """
    request.update_env(user=uid)


class Auth(BaseAuth):
    def _login_ext(self, login, password, context):
        """Authenticate user against Odoo database.

        Uses ``res.users._login`` to validate credentials and
        switches current request environment to authenticated user.

        :param login: User login
        :type login: str
        :param password: User password
        :type password: str
        :param context: Radicale request context
        :type context: Any

        :return: Authenticated login name or empty string if failed
        :rtype: str
        """
        base_env = request.env

        credential = {
            "login": login,
            "password": password,
            "type": "password",
        }

        try:
            res = base_env["res.users"]._login(
                base_env.cr.dbname,
                credential,
                _user_agent_env(context),
            )
        except Exception:
            # Return empty result so Radicale responds with 401 instead of 500
            _logger.info("DAV login failed for %r", login, exc_info=True)
            return ""

        uid = res.get("uid") if isinstance(res, dict) else res
        if not uid:
            return ""

        _set_request_user(base_env, uid)
        return request.env["res.users"].sudo().browse(uid).login or login
