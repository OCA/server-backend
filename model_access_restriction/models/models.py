# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        return super().check_access_rights(operation, raise_exception) and self.env[
            "ir.model.access.restriction"
        ].check_restrictions(self._name, operation, raise_exception)
