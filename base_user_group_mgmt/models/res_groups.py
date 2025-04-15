# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResGroups(models.Model):

    _inherit = "res.groups"

    implied_ids = fields.Many2many(
        readonly=True,
    )
    users = fields.Many2many(
        readonly=True,
    )
    model_access = fields.One2many(
        readonly=True,
    )
    rule_groups = fields.Many2many(
        readonly=True,
    )
