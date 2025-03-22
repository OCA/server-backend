# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AnonymizeMethodRandomString(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.string"
    _description = "Random string"

    def _run(self, field):
        from_clause, where_clause, params = self._get_query(field)
        self.env.cr.execute(
            f"""UPDATE
            {from_clause}
            SET
            {field.field_name}=replace(
                encode((random() * 10)::text::bytea, 'base64'),
                '=', ''
            )
            WHERE
            {where_clause}
            AND {from_clause}.{field.field_name} IS NOT NULL
            """,
            params,
        )
