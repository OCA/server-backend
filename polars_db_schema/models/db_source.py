from odoo import models
from odoo.modules.module import get_module_path
from pathlib import Path


class DfSource(models.Model):
    _inherit = "df.source"

    # def _get_test_file_paths(self):
    #     res = super()._get_test_file_paths()
    #     res.update(
    #         {
    #             "polars_db_schema": {
    #                 "relative_path": "tests/files",
    #                 "xmlid": "migr.contact",
    #             }
    #         }
    #     )
    #     return res
