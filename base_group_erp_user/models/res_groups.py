# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResGroups(models.Model):
    _name = "res.groups"
    _inherit = ["res.groups", "mixin.erp.user.forbidden.fields"]

    @api.model
    def _get_erp_user_system_forbidden_fields(self):
        return [
            "implied_ids",
            "users",
        ]

    @api.model
    def _update_user_groups_view(self):
        """
        Need to bypass security as ERP user can still update groups names and create new ones.
        """
        safe_self = self
        if self._is_current_user_only_erp_user():
            safe_self = self.sudo()
        return super(ResGroups, safe_self)._update_user_groups_view()
