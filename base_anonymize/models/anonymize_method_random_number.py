# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodRandomNumber(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.number"
    _description = "Random number"

    _default_options = {"min_number": 1, "max_number": 9999999}

    def _run(self, field):
        options = field._get_options()
        low, high = int(options["min_number"]), int(options["max_number"])
        return self._update(
            field, SQL("%s + floor(random() * %s)::int", low, high - low + 1)
        )
