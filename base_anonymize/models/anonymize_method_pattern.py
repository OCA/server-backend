# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodPattern(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.pattern"
    _description = "Pattern with record id"

    # {id} becomes the record's id: unique, stable values like partner42@example.com
    _default_options = {"pattern": "anonymized-{id}"}

    def _run(self, field):
        table = SQL.identifier(self._get_model(field)._table)
        return self._update(
            field,
            SQL(
                "replace(%s, '{id}', %s.id::text)",
                field._get_options()["pattern"],
                table,
            ),
        )
