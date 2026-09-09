# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class BaseImportImport(models.TransientModel):
    _inherit = "base_import.import"

    def parse_preview(self, options, count=10):
        res = super().parse_preview(options, count=count)
        if not res.get("error"):
            rules = self.env["base_import.match"].search(
                [("model_name", "=", self.res_model)]
            )
            res["match_fields"] = list(set(rules.mapped("field_ids.name")))
        return res

    def execute_import(self, fields, columns, options, dryrun=False):
        match_only = options.pop("import_match_only_fields", None)
        if match_only is not None:
            self = self.with_context(import_match_only_fields=match_only)
        return super().execute_import(fields, columns, options, dryrun=dryrun)
