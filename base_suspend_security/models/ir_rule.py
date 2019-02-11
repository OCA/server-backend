# © 2015 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models

from ..base_suspend_security import BaseSuspendSecurityUid


class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def domain_get(self, model_name, mode='read'):
        if isinstance(self.env.uid, BaseSuspendSecurityUid):
            return [], [], ['"%s"' % self.pool[model_name]._table]
        return super(IrRule, self).domain_get(model_name, mode=mode)
