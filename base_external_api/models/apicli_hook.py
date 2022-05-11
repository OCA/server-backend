# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ApicliHook(models.Model):
    _name = "apicli.hook"
    _description = "API Client Hook"
    _order = "sequence, name"

    name = fields.Char()
    sequence = fields.Integer()
    model_id = fields.Many2one("ir.model")
    match_regexp = fields.Char()
    method_name = fields.Char()
