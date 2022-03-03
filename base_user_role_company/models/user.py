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
        # Enable only the Roles corresponing to the currently selected company
        if self.role_line_ids:
            res = res.filtered(
                lambda x: not x.company_id or x.company_id == self.env.company
            )
        return res

    def set_groups_from_roles(self, force=False, company_id=False):
        # When using the Company Switcher widget, the self.env.company is not yet set
        if company_id:
            self = self.with_company(company_id)
        return super().set_groups_from_roles(force=force)
