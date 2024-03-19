# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("navigate", "Navigate")], ondelete={"navigate": "set default"}
    )

    navigate_line_ids = fields.One2many(
        comodel_name="ir.actions.server.navigate.line",
        string="Navigate Lines",
        inverse_name="action_id",
    )

    navigate_action_id = fields.Many2one(
        string="Navigation Action",
        comodel_name="ir.actions.act_window",
        domain="[('res_model', '=', navigate_model_technical_name)]",
        help="Define here the action used when the navigation will be executed"
        " if empty, a generic action will be used.",
    )

    navigate_model_id = fields.Many2one(
        string="Final Navigation Model",
        comodel_name="ir.model",
        compute="_compute_navigate_infos",
    )

    navigate_model_technical_name = fields.Char(
        compute="_compute_navigate_infos",
    )

    @api.depends("navigate_line_ids.field_id", "model_id")
    def _compute_navigate_infos(self):
        IrModel = self.env["ir.model"]
        for action in self:
            if action.navigate_line_ids:
                action.navigate_model_id = IrModel.search(
                    [("model", "=", action.navigate_line_ids[-1].field_id.relation)]
                )
            else:
                action.navigate_model_id = action.model_id
            action.navigate_model_technical_name = action.navigate_model_id.model

    def delete_last_line(self):
        self.ensure_one()
        self.navigate_line_ids[-1].unlink()
        self.navigate_action_id = False

    def _run_action_navigate_multi(self, eval_context=None):
        self.ensure_one()
        lines = self.navigate_line_ids
        if not lines:
            raise UserError(
                _("The Action Server %s is not correctly set\n : No fields defined")
                % (self.name)
            )
        mapped_field_value = ".".join(lines.mapped("field_id.name"))

        item_ids = eval_context["records"].mapped(mapped_field_value).ids
        domain = "[('id','in',[" + ",".join(map(str, item_ids)) + "])]"

        if self.navigate_action_id:
            # Use Defined action if defined
            return_action = self.navigate_action_id
            result = return_action.read()[0]
            result["domain"] = domain
        else:
            # Otherwise, return a default action
            result = {
                "name": self.navigate_model_id.name,
                "domain": domain,
                "res_model": self.navigate_model_id.model,
                "target": "current",
                "type": "ir.actions.act_window",
                "view_mode": "tree,form",
            }

        return result
