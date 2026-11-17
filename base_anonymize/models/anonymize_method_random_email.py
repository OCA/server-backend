# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodRandomEmail(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.email"
    _description = "Random email"

    def _run(self, field):
        return self._update(
            field,
            SQL(
                "substring(encode((random() * 10000)::text::bytea, 'base64'), "
                "1, 5 + (random() * 10)::int) || '@example.com'"
            ),
        )
