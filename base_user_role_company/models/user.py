# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2026 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class ResUsers(models.Model):
    _inherit = "res.users"

    def authenticate(self, *args, **kwargs):
        auth_info = super().authenticate(*args, **kwargs)
        # Ensure proper roles are applied for the logged-in user
        uid = auth_info.get("uid") if isinstance(auth_info, dict) else None
        if uid:
            env = api.Environment(self.env.cr, uid, {})
            if env.user.role_line_ids:
                env.user.set_groups_from_roles()
        return auth_info

    def _get_enabled_roles(self):
        """Write `res.users::group_ids` with the groups of user's default `company_id`.
        This is NOT used for access right/rule check but only for presentation in user's
        form"""
        res = super()._get_enabled_roles()
        return res.filtered(
            lambda role_line: not role_line.company_id
            or self.company_id == role_line.company_id
        )

    def _get_company_aware_roles(self, *args, **kwargs):
        """Return the roles company-aware. If several companies are active, only return
        the INTERSECTION of the roles possible in these companies. This prevents
        extending a role initially given in a Company A to a company B when a user
        is browsing with the 2 companies active.
        """
        if not self.role_line_ids:
            return self.env["res.users.role.line"]

        company_roles_lines = self.role_line_ids.filtered("company_id")
        global_roles_lines = self.role_line_ids - company_roles_lines
        company_roles_lines_intersect = company_roles_lines.browse()
        for role_lines in company_roles_lines.grouped("role_id").values():
            if set(self.env.companies.ids) <= set(role_lines.company_id.ids):
                company_roles_lines_intersect |= role_lines

        return global_roles_lines | company_roles_lines_intersect

    @tools.ormcache("self.id", "tuple(self.env.companies.ids)")
    def _get_group_ids(self):
        """ORM override WITHOUT calling super(), else it returns parent cache
        We add 'self.env.companies.ids' in @tools.ormcache.
        To keep synched with: addons/base/models/res_users::_get_group_ids"""
        self.ensure_one()
        return self.all_group_ids._ids

    @api.depends("group_ids.all_implied_ids", "role_line_ids.company_id")
    @api.depends_context("allowed_company_ids")
    def _compute_all_group_ids(self):
        """Override: compute users groups implited by company-aware roles"""
        user_with_roles = self.filtered("role_line_ids")
        res = super(ResUsers, self - user_with_roles)._compute_all_group_ids()
        for user in user_with_roles:
            user.all_group_ids = user._get_company_aware_roles().role_id.all_implied_ids
        return res
