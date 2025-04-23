# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model
    def _get_erp_user_system_forbidden_fields(self):
        return [
            "role_ids",
            "parent_ids",
            *super()._get_erp_user_system_forbidden_fields(),
        ]
