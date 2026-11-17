# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodSetNull(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.set.null"
    _description = "Set null"

    def _run(self, field):
        if not self._is_stored(field):
            # binary fields in attachments: let the ORM drop the files
            records = self._get_model(field).search(field._get_domain())
            records.write({field.field_name: False})
            return len(records)
        return self._update(field, SQL("NULL"))
