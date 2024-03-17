# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        uid = super().authenticate(db, login, password, user_agent_env)
        # On login, ensure the proper roles are applied
        # The last Role applied may not be the correct one,
        # sonce the new session current company can be different
        with cls.pool.cursor() as cr:
            env = api.Environment(cr, uid, {})
            if env.user.role_line_ids:
                env.user.set_groups_from_roles()
        return uid

    def _get_enabled_roles(self):
        res = super()._get_enabled_roles()
        if self.role_line_ids:
            active_roles = self.env["res.users.role.line"]
            if self.env.context.get("active_company_ids"):
                company_ids = self.env.context.get("active_company_ids")
            else:
                company_ids = self.company_id.ids
            for role_line in self.role_line_ids:
                if not role_line.company_id:
                    active_roles |= role_line
                elif role_line.company_id.id in company_ids:
                    role_line_companies = self.role_line_ids.filtered(
                        lambda x: x.role_id == role_line.role_id
                        and x.company_id.id in company_ids
                    )
                    if len(role_line_companies) == len(company_ids):
                        active_roles |= role_line
            return active_roles
        return res
