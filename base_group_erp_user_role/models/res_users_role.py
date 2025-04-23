# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResUsersRole(models.Model):
    _name = "res.users.role"
    _inherit = ["res.users.role", "mixin.erp.user.forbidden.fields"]

    @api.model
    def _get_erp_user_system_forbidden_fields(self):
        return [
            "implied_ids",
            "line_ids",
        ]
