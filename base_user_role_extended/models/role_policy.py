# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    exclude_from_role_policy = fields.Boolean(
        compute="_compute_exclude_from_role_policy", store=True
    )

    @api.depends("login")
    def _compute_exclude_from_role_policy(self):
        for user in self:
            if user in (
                self.env.ref("base.user_admin"),
                self.env.ref("base.user_root"),
            ):
                user.exclude_from_role_policy = True
            else:
                user.exclude_from_role_policy = False
