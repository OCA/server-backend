# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class AnonymizeMethodFictionalCharacterData(models.Model):
    _name = "anonymize.method.fictional.character.data"
    _description = "Fictional character"

    name = fields.Char()
