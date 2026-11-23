# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class ResUsers(models.Model):
    _inherit = "res.users"

    bypass_role_policy = fields.Boolean(
        compute="_compute_bypass_role_policy",
        help="If checked, this record bypasses role-based"
        "view combination evaluation checks",
    )

    def _compute_bypass_role_policy(self):
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)
        root = self.env.ref("base.user_root", raise_if_not_found=False)
        for user in self:
            user.bypass_role_policy = user in (admin, root)

    def set_groups_from_roles(self, force=False):
        # Admin / root users should not have their actual groups replaced by roles
        # because they bypass role policy and rely on their standard groups.
        users_to_update = self.filtered(lambda u: not u.bypass_role_policy)
        if users_to_update:
            return super(ResUsers, users_to_update).set_groups_from_roles(force=force)
        return True

    @tools.ormcache("self.id", "self.env.uid", "self.env.context.get('role')")
    def _get_group_ids(self):
        if self.env.context.get("role"):
            if not self.bypass_role_policy:
                enabled_roles = self._get_enabled_roles()
                if enabled_roles:
                    groups = enabled_roles.mapped("role_id.group_id")
                    return groups._ids
        return super()._get_group_ids()
