import logging

from odoo import exceptions, models

PREFIX = "any"
logger = logging.getLogger(__name__)


class UpsertMixin(models.AbstractModel):
    _name = "upsert.mixin"
    _description = "Allow to insert ou update records"

    def get_id_strings(self, module=PREFIX):
        return {
            x.name: x.model
            for x in self.env["ir.model.data"].search([("module", "=", module)])
        }

    def _upsert_record(self, model, id_string, values, module=PREFIX):
        """Create or update a record matching xmlid with values
        Code from Anthem lib
        """
        if "." in id_string:
            raise exceptions.ValidationError(
                f"xmlid '{id_string}' shouldn't contains dot '.'"
            )
        if isinstance(model, str):
            model = self.env[model]

        record = self.env.ref(f"{module}.{id_string}", raise_if_not_found=False)
        if record:
            record.update(values)
        else:
            record = model.create(values)
            self.add_xmlid(record, id_string, module)
        return id_string

    def add_xmlid(self, record, id_string, module, noupdate=False):
        """Add a XMLID on an existing record
        Code from Anthem lib
        """
        ir_model_data = self.env["ir.model.data"]
        try:
            if hasattr(ir_model_data, "xmlid_lookup"):
                # Odoo version <= 14.0
                ref_id, __, __ = ir_model_data.xmlid_lookup(f"{module}.{id_string}")
            else:
                # Odoo version >= 15.0
                ref_id, __, __ = ir_model_data._xmlid_lookup(f"{module}.{id_string}")
        except ValueError:
            logger.info("Odoo Version unknow version")
            pass  # does not exist, we'll create a new one
        else:
            return ir_model_data.browse(ref_id)
        return self.env["ir.model.data"].create(
            {
                "name": id_string,
                "module": module,
                "model": record._name,
                "res_id": record.id,
                "noupdate": noupdate,
            }
        )
