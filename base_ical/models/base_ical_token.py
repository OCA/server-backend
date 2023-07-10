# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


import secrets

from odoo import fields, models


class BaseIcalToken(models.Model):
    _name = "base.ical.token"
    _description = "User token of an iCal export"
    _rec_name = "ical_id"

    active = fields.Boolean(default=True)
    ical_id = fields.Many2one("base.ical", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")
    token = fields.Char(required=True, default=lambda self: secrets.token_urlsafe())

    _sql_constraints = [
        ("token_uniqe", "unique(token)", "The token must be unique"),
    ]
