# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodRandomString(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.string"
    _description = "Random string"

    def _run(self, field):
        return self._update(
            field,
            SQL("replace(encode((random() * 10)::text::bytea, 'base64'), '=', '')"),
        )
