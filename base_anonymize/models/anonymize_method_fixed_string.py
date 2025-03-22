# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class AnonymizeMethodFixedString(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.fixed.string"
    _description = "Fixed string"

    string = fields.Text(required=True, default="-anonymized-")

    def _run(self, field):
        options = field._get_options()
        from_clause, where_clause, params = self._get_query(field)
        self.env.cr.execute(
            f"""UPDATE
            {from_clause}
            SET
            {field.field_name}=%s
            WHERE
            {where_clause}
            AND {from_clause}.{field.field_name} IS NOT NULL
            """,
            [options["string"]] + params,
        )
