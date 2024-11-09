from odoo import models


class DfSource(models.Model):
    _inherit = "df.source"

    # def _get_modules_w_df_files(self):
    #     res = super()._get_modules_w_df_files()
    #     res.update(
    #         {
    #             "polars_db_schema": {
    #                 "xmlid": "migr.contact",
    #             }
    #         }
    #     )
    #     return res
