# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_default_profile(self):
        return self.env.ref("base_user_role_profile.default_profile")

    profile_id = fields.Many2one(
        "res.users.profile",
        "Current profile",
        default=lambda self: self._get_default_profile,
    )

    profile_ids = fields.Many2many(
        "res.users.profile", string="Currently allowed profiles",
    )

    def _get_action_root_menu(self):
        # used JS-side. Reload the client; open the first available root menu
        menu = self.env["ir.ui.menu"].search([("parent_id", "=", False)])[:1]
        return {
            "type": "ir.actions.client",
            "tag": "reload",
            "params": {"menu_id": menu.id},
        }

    def action_profile_change(self, vals):
        self.write(vals)
        return self._get_action_root_menu()

    @api.model
    def create(self, vals):
        new_record = super().create(vals)
        if vals.get("company_id") or vals.get("role_line_ids"):
            new_record.sudo()._compute_profile_ids()
        return new_record

    def write(self, vals):
        # inspired by base/models/res_users.py l. 491
        if self == self.env.user and vals.get("profile_id"):
            self.sudo().write({"profile_id": vals["profile_id"]})
            del vals["profile_id"]
        res = super().write(vals)
        if (
            vals.get("company_id")
            or vals.get("profile_id")
            or vals.get("role_line_ids")
        ):
            self.sudo()._compute_profile_ids()
        return res

    def _get_applicable_roles(self):
        res = super()._get_applicable_roles()
        res = res.filtered(
            lambda r: not r.profile_id
            or (r.profile_id.id == r.user_id.profile_id.id)
        )
        return res

    def _update_profile_id(self):
        default_profile = self.env.ref(
            "base_user_role_profile.default_profile"
        )
        if not self.profile_ids:
            if self.profile_id != default_profile:
                self.profile_id = default_profile
        elif self.profile_id not in self.profile_ids:
            self.write({"profile_id": self.profile_ids[0].id})

    def _compute_profile_ids(self):
        for rec in self:
            role_lines = rec.role_line_ids
            profiles = role_lines.filtered(
                lambda r: r.company_id == rec.company_id
            ).mapped("profile_id")
            rec.profile_ids = profiles
            # set defaults in case applicable profile changes
            rec._update_profile_id()
