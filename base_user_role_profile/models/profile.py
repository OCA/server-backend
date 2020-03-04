# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUsersProfile(models.Model):
    _name = "res.users.profile"
    _description = "Role profile"

    name = fields.Char("Name")
    user_ids = fields.Many2many(
        "res.users", string="Allowed users", compute="_compute_user_ids"
    )
    role_ids = fields.One2many("res.users.role", "profile_id", string="Roles")

    def _compute_user_ids(self):
        for rec in self:
            rec.user_ids = self.env["res.users"].search(
                [("profile_ids", "in", rec.ids)]
            )
