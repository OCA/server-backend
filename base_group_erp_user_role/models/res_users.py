# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _default_role_lines(self):
        if self._is_current_user_only_erp_user():
            return []
        return super()._default_role_lines()

    @api.model
    def _get_erp_user_system_forbidden_fields(self):
        return ["role_line_ids", *super()._get_erp_user_system_forbidden_fields()]
