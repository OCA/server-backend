from odoo import fields, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    view_access = fields.Many2many(
        groups="base.group_system",
    )
