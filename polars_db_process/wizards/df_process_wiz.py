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
            if self.model_map_id.action == "import":
                self._odoo_data_import(df)

    def _odoo_data_import(self, df):
        model = self.model_map_id.model_id.model
        vals_list = df.to_dicts()
        mapper = {}
        rebellious = {}
        for vals in vals_list:
            for key in self.env["model.map"]._get_touchy_fields_to_import().get(model):
                if key in vals:
                    rebellious[key] = vals.pop(key)
            uidstring = vals.pop("id")
            nvals = {
                x: val for x, val in vals.items() if x in self.env[model]._fields.keys()
            }
            if "parent_id" in nvals:
                # here for product.category
                # TODO move this specific behavior elsewhere
                nvals["parent_id"] = mapper.get(nvals["parent_id"])
            rec = self.env[model].create(nvals)
            mapper[uidstring] = rec.id
            logger.info(f"  >>> {vals}")
            self._set_uidstring(uidstring, rec, model)
            self._process_touchy_fields(rec, rebellious)

    def _set_uidstring(self, uidstring, record, model):
        """Create Unique Id String also know as XmlId in the Odoo world,
        even if not really xml ;-)"""
        self.env["ir.model.data"].create(
            {
                "res_id": record.id,
                "model": model,
                "module": self.model_map_id._get_uidstring_module_name(),
                "name": uidstring,
                "noupdate": False,
            }
        )

    def _process_touchy_fields(self, record, rebellious):
        """Override Suggestion:
        self._touchy_fields_fallback(record, rebellious)
        or any other alternative
        """

    def _touchy_fields_fallback(self, record, rebellious):
        for key in rebellious:
            try:
                record[key] = rebellious[key]
            except Exception:
                logger.warning(f"\n\n\n\n\nPb here {rebellious[key]}")
                continue
