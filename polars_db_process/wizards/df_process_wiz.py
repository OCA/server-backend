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
        touchy = {}
        if model == "product.product":
            categs = {
                x.name: x.res_id
                for x in self._get_ir_model_data("product.category", "cat-")
            }
        if model == "res.partner" and "livr.sql" in self.df_source_id.name:
            parents = {
                x.name: x.res_id
                for x in self._get_ir_model_data("res.partner", "societe")
            }
        cpt = 0
        for vals in vals_list:
            # if cpt == 200:
            #     self.env.cr.commit()
            #     logger.info("200 created")
            #     cpt = 0
            touchy_model = (
                self.env["model.map"]._get_touchy_fields_to_import().get(model)
            )
            if touchy_model:
                for key in (
                    self.env["model.map"]._get_touchy_fields_to_import().get(model)
                ):
                    if key in vals:
                        touchy[key] = vals.pop(key)
            uidstring = vals.pop("id")
            nvals = {
                x: val for x, val in vals.items() if x in self.env[model]._fields.keys()
            }
            if "categ_id" in nvals:
                nvals["categ_id"] = categs.get(nvals["categ_id"]) or 1
            if "parent_id" in nvals:
                # here for product.category
                # TODO move this specific behavior elsewhere
                if model == "res.partner":
                    nvals["parent_id"] = parents.get(nvals["parent_id"])
                if model == "product.category":
                    nvals["parent_id"] = mapper.get(nvals["parent_id"])
            rec = self.env[model].create(nvals)
            if model == "product.category":
                mapper[uidstring] = rec.id
            self._set_unique_idstring(uidstring, rec, model)
            self._process_touchy_fields(rec, touchy)
            cpt += 1

    def _set_unique_idstring(self, uidstring, record, model):
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

    def _get_ir_model_data(self, model, string, module=None):
        module = module or self.env["db.config"]._set_uidstring_module_name()
        return self.env["ir.model.data"].search(
            [
                ("module", "=", module),
                ("model", "=", model),
                ("name", "ilike", f"%{string}%"),
            ]
        )

    def _process_touchy_fields(self, record, touchy):
        """Override Suggestion:
        self._touchy_fields_fallback(record, touchy)
        or any other alternative
        """

    def _touchy_fields_fallback(self, record, touchy):
        for key in touchy:
            try:
                record[key] = touchy[key]
            except Exception:
                logger.warning(f"\n\n\n\n\nCarefull here {touchy[key]}")
                continue
