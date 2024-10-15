# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    profile_id = fields.Many2one(
        "res.users.profile",
        "Profile",
    )

    def write(self, vals):
        res = super().write(vals)
        if "profile_id" in vals:
            # update the user's allowed profiles
            self.user_ids._compute_profile_ids()
        return res


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    profile_id = fields.Many2one(related="role_id.profile_id")
