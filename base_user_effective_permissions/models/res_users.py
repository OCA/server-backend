# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import _, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def action_show_effective_permissions(self):
        self.ensure_one()
        permissions = self.env["res.users.effective.permission"]._generate_permissions(
            self
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Effective permissions for %s") % self.name,
            "res_model": "res.users.effective.permission",
            "view_mode": "tree",
            "domain": [("id", "in", permissions.ids)],
        }
