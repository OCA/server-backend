# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, SUPERUSER_ID

from ..base_suspend_security import BaseSuspendSecurityUid


class Base(models.AbstractModel):

    _inherit = 'base'

    @api.model
    def suspend_security(self):
        return self.with_env(
            api.Environment(
                self.env.cr,
                BaseSuspendSecurityUid(self.env.uid),
                self.env.context))

    def sudo(self, user=SUPERUSER_ID):
        if isinstance(user, BaseSuspendSecurityUid):
            return self.with_env(
                api.Environment(
                    self.env.cr, user, self.env.context
                )
            )
        return super().sudo(user)

    @api.model
    def check_field_access_rights(self, operation, fields):
        # Handle suspend_security as if called with SUPERUSER_ID
        if isinstance(self.env.uid, BaseSuspendSecurityUid):
            return fields or list(self._fields)

        return super().check_field_access_rights(operation, fields)
