# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AnonymizeMethodFictionalCharacter(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.fictional.character"
    _description = "Fictional character"

    def _run(self, field):
        Names = self.env["anonymize.method.fictional.character.data"]
        names_count = Names.search_count([])
        from_clause, where_clause, params = self._get_query(field)
        self.env.cr.execute(
            f"""
            WITH __names AS (
                SELECT
                row_number() OVER () id,
                name
                FROM
                anonymize_method_fictional_character_data
            )
            UPDATE
            {from_clause}
            SET
            {field.field_name}=__names.name
            FROM
            __names
            WHERE
            {from_clause}.id % {names_count} = __names.id
            AND {from_clause}.{field.field_name} IS NOT NULL
            AND {where_clause}
            """,
            params,
        )
