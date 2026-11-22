# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AnonymizeMethodRecompute(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.recompute"
    _description = "Recompute stored computed field"

    def _run(self, field):
        """For stored copies of anonymized values (complete_name,
        email_normalized...): give them a higher sequence than their sources."""
        model = self._get_model(field)
        model_field = model._fields[field.field_name]
        if not (model_field.store and model_field.compute):
            return 0
        self.env.invalidate_all()
        records = model.search(field._get_domain())
        self.env.add_to_compute(model_field, records)
        model.flush_model([field.field_name])
        return len(records)
