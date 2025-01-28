# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    last_role_line_modification = fields.Datetime(
        compute="_compute_last_role_line_modification",
    )

    def _compute_last_role_line_modification(self):
        for user in self:
            res = self.env["base.user.role.line.history"].search(
                [("user_id", "=", user.id)], limit=1, order="id desc"
            )
            user.last_role_line_modification = res.create_date if res else False

    def show_role_lines_history(self):  # pragma: no cover
        self.ensure_one()
        domain = [("user_id", "=", self.id)]
        return {
            "name": self.env._("Roles history"),
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "base.user.role.line.history",
            "domain": domain,
        }
