from odoo import _, exceptions, models


class DfProcessWiz(models.TransientModel):
    _inherit = "df.process.wiz"

    def _pre_process(self):
        res = super()._pre_process()
        if not self.file:
            self._pre_process_sql()
        return res

    def _pre_process_sql(self):
        "You may inherit to set your own behavior"
        if not self.df_source_id.db_conf_id:
            raise exceptions.ValidationError(
                _("Missing database configuration in your df source ")
            )
        self._process_sql()

    def _process_sql(self):
        self.ensure_one()
        df = self.df_source_id.db_conf_id._read_sql(self.df_source_id.query)
        if self.dataframe_id:
            self.env[self.dataframe_id.model_id.model].create(df.to_dicts())
