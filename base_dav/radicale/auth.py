# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo.http import request

try:
    from radicale.auth import BaseAuth
except ImportError:
    BaseAuth = object

_logger = logging.getLogger(__name__)


class Auth(BaseAuth):
    def _login(self, login: str, password: str) -> str:
        """Authenticate user against Odoo."""
        if not login or not password:
            return ""
        try:
            env = request.env
            uid = env["res.users"]._login(env.cr.dbname, login, password)
            if uid:
                request.update_env(user=uid)
                return login
        except Exception:
            _logger.debug("DAV authentication failed for %s", login, exc_info=True)
        return ""

    def get_external_login(self, environ):
        return ()
