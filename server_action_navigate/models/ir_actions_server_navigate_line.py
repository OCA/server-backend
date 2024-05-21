# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class IrActionsServerNavigateLine(models.Model):
    _name = "ir.actions.server.navigate.line"
    _description = "Server Actions Navigation Lines"
    _order = "id"

    action_id = fields.Many2one(
        comodel_name="ir.actions.server",
        string="Action",
        required=True,
        ondelete="cascade",
    )

    field_domain_model_id = fields.Many2one(
        string="Field Model",
        comodel_name="ir.model",
        ondelete="cascade",
        compute="_compute_field_domain_model_id",
        help="Technical field, used as a domain for the 'field' field.",
    )

    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        ondelete="cascade",
        domain="["
        "('model_id', '=', field_domain_model_id),"
        " ('ttype', 'in', ['many2one', 'one2many', 'many2many']),"
        "]",
        required=True,
    )

    @api.depends("action_id.navigate_line_ids.field_id")
    def _compute_field_domain_model_id(self):
        IrModel = self.env["ir.model"]
        for line in self:
            model = self.action_id.model_id
            for action_line in self.action_id.navigate_line_ids:
                if action_line == line:
                    line.field_domain_model_id = model
                    break
                model = IrModel.search([("model", "=", action_line.field_id.relation)])
