# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.http import request

try:
    from radicale.auth import BaseAuth
except ImportError:
    BaseAuth = None


class Auth(BaseAuth):
    def is_authenticated2(self, login, user, password):
        env = request.env
        uid = env['res.users']._login(env.cr.dbname, user, password)
        if uid:
            request._env = env(user=uid)
        return bool(uid)
