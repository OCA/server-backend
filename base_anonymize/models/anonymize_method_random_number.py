# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class AnonymizeMethodRandomNumber(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.number"
    _description = "Random number"

    min_number = fields.Integer(required=True, default=1)
    max_number = fields.Integer(required=True, default=9999999)

    def _run(self, field):
        options = field._get_options()
        from_clause, where_clause, params = self._get_query(field)
        self.env.cr.execute(
            f"""UPDATE
            {from_clause}
            SET
            {field.field_name}={options['min_number']} + (
                random() * {options['max_number'] - options['min_number']}
            )
            WHERE
            {where_clause}
            AND {from_clause}.{field.field_name} IS NOT NULL
            """,
            params,
        )
