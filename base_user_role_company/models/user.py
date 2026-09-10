# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


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

    def _get_enabled_roles(self, *args, **kwargs):
        """Return the roles company-aware. If several companies are active, only return
        the INTERSECTION of the roles possible in these companies. This prevents
        extending a role initially given in a Company A to a company B when a user
        is browsing with the 2 companies active.
        """
        res = super()._get_enabled_roles(*args, **kwargs)
        if not self.role_line_ids:
            return res

        if self.env.context.get("active_company_ids"):
            company_ids = set(self.env.context.get("active_company_ids"))
        else:
            company_ids = set(self.company_id.ids)

        company_roles_lines = res.filtered("company_id")
        global_roles_lines = res - company_roles_lines
        company_roles_lines_intersect = company_roles_lines.browse()
        for role_lines in company_roles_lines.grouped("role_id").values():
            role_line_companies = self.role_line_ids.filtered(
                lambda x, rl=role_lines: x.role_id == rl.role_id
            )
            if company_ids <= set(role_line_companies.mapped("company_id").ids):
                company_roles_lines_intersect |= role_lines

        return global_roles_lines | company_roles_lines_intersect
