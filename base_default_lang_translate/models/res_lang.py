# Copyright 2021 Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResLang(models.Model):
    _inherit = "res.lang"

    is_default_lang = fields.Boolean("Default Language", default=False)

    @api.constrains("is_default_lang")
    def _check_default(self):
        if self.search_count([("is_default_lang", "=", True)]) > 1:
            raise ValidationError(_("Another language is already set by default"))
