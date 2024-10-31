from odoo import models


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
