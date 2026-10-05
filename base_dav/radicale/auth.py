# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from radicale.auth import BaseAuth

from odoo.http import request

_logger = logging.getLogger(__name__)


class Auth(BaseAuth):
    def _login_ext(self, login, password, context):
        """Authenticate DAV user with an Odoo API key."""
        del context

        if not login or not password:
            return ""

        env = request.env
        uid = env["res.users.apikeys"]._check_credentials(
            scope="dav",
            key=password,
        )
        if not uid:
            _logger.info(f"DAV login failed for {login}")
            return ""

        user = env["res.users"].sudo().browse(uid)
        if not user.exists() or user.login != login:
            _logger.info(f"DAV login failed for {login}")
            return ""

        request.update_env(user=uid)
        return user.login
