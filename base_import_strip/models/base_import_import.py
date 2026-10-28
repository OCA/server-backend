# Copyright 2026 - GRAP - Sylvain LE GAL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class BaseImportImport(models.TransientModel):
    _inherit = "base_import.import"

    def _read_file(self, options):
        nb_rows, rows = super()._read_file(options)
        if not self.env.context.get("base_import_strip_disabled"):
            rows = [[x.strip() for x in row] for row in rows]
        return nb_rows, rows
