# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodFictionalCharacter(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.fictional.character"
    _description = "Fictional character"

    def _run(self, field):
        names_count = self.env[
            "anonymize.method.fictional.character.data"
        ].search_count([])
        if not names_count:
            return 0
        table = SQL.identifier(self._get_model(field)._table)
        return self._update(
            field,
            SQL("__names.name"),
            from_clause=SQL(
                "(SELECT row_number() OVER (ORDER BY id) - 1 AS pos, name "
                "FROM anonymize_method_fictional_character_data) AS __names"
            ),
            # row_number() - 1 runs from 0, as the modulo does
            where=SQL("mod(%s.id, %s) = __names.pos", table, names_count),
        )
