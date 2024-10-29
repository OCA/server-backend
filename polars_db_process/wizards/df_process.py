import logging

from odoo import _, exceptions, models

logger = logging.getLogger(__name__)


class DfProcessWiz(models.TransientModel):
    _inherit = "df.process.wiz"

    def _pre_process(self):
        res = super()._pre_process()
        if not self.file:
            self._pre_process_query()
        return res

    def _pre_process_query(self):
        "You may inherit to set your own behavior"
        if not self.df_source_id.db_conf_id:
            raise exceptions.ValidationError(
                _("Missing database configuration in your df source ")
            )
        self._process_query()

    def _process_query(self):
        self.ensure_one()
        df = self.df_source_id.db_conf_id._read_sql(self.df_source_id.query)
        if self.model_map_id:
            model = self.model_map_id.model_id.model
            vals_list = df.to_dicts()
            mapper = {}
            for vals in vals_list:
                uidstring = vals.pop("id")
                if "parent_id" in vals:
                    vals["parent_id"] = mapper.get(vals["parent_id"])
                rec = self.env[model].create(vals)
                mapper[uidstring] = rec.id
                logger.info("  >>>  ", vals)
                self._set_uidstring(uidstring, rec, model)

    def _set_uidstring(self, uidstring, record, model):
        self.env["ir.model.data"].create(
            {
                "res_id": record.id,
                "model": model,
                "module": self.model_map_id._get_uidstring_module_name(),
                "name": uidstring,
                "noupdate": False,
            }
        )
