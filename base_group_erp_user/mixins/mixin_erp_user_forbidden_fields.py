import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MixinErpUserForbiddenFields(models.AbstractModel):
    _name = "mixin.erp.user.forbidden.fields"
    _description = "Mixin ERP User Forbidden Fields"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._remove_erp_user_system_forbidden_fields(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._remove_erp_user_system_forbidden_fields(vals)
        return super().write(vals)

    @api.model
    def _get_erp_user_system_forbidden_fields(self):
        return []

    @api.model
    def _is_current_user_only_erp_user(self):
        return self.env.user._is_user_only_erp_user()

    @api.model
    def _remove_erp_user_system_forbidden_fields(self, values):
        if not self._is_current_user_only_erp_user():
            return
        for fname in self._get_erp_user_system_forbidden_fields():
            values.pop(fname, False)
