# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AnonymizeMethodRandomEmail(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.email"
    _description = "Random email"

    def _run(self, field):
        from_clause, where_clause, params = self._get_query(field)
        self.env.cr.execute(
            f"""UPDATE
            {from_clause}
            SET
            {field.field_name}=substring(
                encode((random() * 10000)::text::bytea, 'base64'),
                1,
                5 + (random() * 10)::int
            ) || '@example.com'
            WHERE
            {where_clause}
            AND {from_clause}.{field.field_name} IS NOT NULL
            """,
            params,
        )
