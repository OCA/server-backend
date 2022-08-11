# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class IrActionsServerNavigateLine(models.Model):
    _name = "ir.actions.server.navigate.line"
    _description = "Server Actions Navigation Lines"
    _order = "sequence, id"

    sequence = fields.Integer(string="Sequence")

    field_model = fields.Char(string="Model", related="field_id.relation", store=True)

    action_id = fields.Many2one(
        comodel_name="ir.actions.server",
        string="Action",
        required=True,
        ondelete="cascade",
    )

    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Field",
        required=True,
        ondelete="cascade",
    )

    # when adding a record, onchange is called for every field on the
    # form, also in editable list views
    @api.onchange("field_id")
    def _onchange_field_id(self):

        lines = self.action_id.new(
            {"navigate_line_ids": self.env.context.get("navigate_line_ids", [])}
        ).navigate_line_ids

        model = lines[-1:].field_id.relation or self.action_id.model_id.model
        return {
            "domain": {
                "field_id": [
                    ("ttype", "in", ["many2one", "one2many", "many2many"]),
                    ("model", "=", model),
                ],
            }
        }
