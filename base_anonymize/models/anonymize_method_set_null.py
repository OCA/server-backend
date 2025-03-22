# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools.safe_eval import const_eval


class AnonymizeMethodSetNull(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.set.null"
    _description = "Set null"

    def _run(self, field):
        model = self.env[field.model_name].with_context(active_test=False)
        if not model._fields[field.field_name].store:
            model.sudo().search(const_eval(field.domain or "[]")).write(
                {
                    field.field_name: False,
                }
            )
            return

        from_clause, where_clause, params = self._get_query(field)
        self.env.cr.execute(
            f"""UPDATE
            {from_clause}
            SET
            {field.field_name}=NULL
            WHERE
            {where_clause}
            """,
            params,
        )
