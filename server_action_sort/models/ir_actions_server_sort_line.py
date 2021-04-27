# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class IrActionsServerNavigateLine(models.Model):
    _name = "ir.actions.server.sort.line"
    _description = "Server Actions Sort Lines"
    _order = "sequence"

    sequence = fields.Integer(string="Sequence")

    action_id = fields.Many2one(
        comodel_name="ir.actions.server", string="Action",
        required=True, ondelete="cascade")

    field_id = fields.Many2one(
        comodel_name='ir.model.fields', string='Field', required=True,
        domain="[('model', '=', parent.sort_field_id_model)]")

    field_name = fields.Char(
        string="Field Name", related="field_id.name")

    desc = fields.Boolean(string='Inverse Order')
