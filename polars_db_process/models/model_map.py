from odoo import models


class ModelMap(models.Model):
    _inherit = "model.map"

    def _remove_related_uidstring_record(self):
        self = self.browse(self.env.context.get("active_ids"))
        self = self and self[0] or False
        res = self.env["ir.model.data"].search(
            [
                ("model", "=", self.model_id.model),
                ("module", "=", self._get_uidstring_module_name()),
            ]
        )
        res.reference.unlink()
        return True

    def _get_uidstring_module_name(self):
        return "polars"
