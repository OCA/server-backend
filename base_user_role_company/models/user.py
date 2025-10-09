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
        res = super()._get_enabled_roles(*args, **kwargs)
        if self.role_line_ids:
            active_roles = self.env["res.users.role.line"]
            if self.env.context.get("active_company_ids"):
                company_ids = self.env.context.get("active_company_ids")
            else:
                company_ids = self.company_id.ids
            for role_line in res:
                if not role_line.company_id:
                    active_roles |= role_line
                elif role_line.company_id.id in company_ids:
                    role_line_companies = self.role_line_ids.filtered(
                        lambda x, rl=role_line: (
                            x.role_id == rl.role_id and x.company_id.id in company_ids
                        )
                    )
                    if len(role_line_companies) == len(company_ids):
                        active_roles |= role_line
            return active_roles
        return res
