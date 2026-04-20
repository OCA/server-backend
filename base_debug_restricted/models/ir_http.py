# Copyright 2026 QoQa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _handle_debug(cls):
        if request.httprequest.args.get("debug") is None:
            return

        if not cls._debug_mode_allowed_users():
            request.session.debug = ""
            return

        return super()._handle_debug()

    @classmethod
    def _debug_mode_allowed_users(cls):
        if not request.session.uid:
            # always disallowed in public
            return False
        user = request.env["res.users"].browse(request.session.uid)
        return user.sudo().has_group("base_debug_restricted.group_debug_mode")
