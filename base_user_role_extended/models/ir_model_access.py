# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    @tools.ormcache("self.env.uid", "mode")
    def _get_allowed_models(self, mode="read"):
        """
        Override to enforce exclusive role-based model access.
        """
        self = self.with_context(role=True)
        return super()._get_allowed_models(mode)

    # Handle access rights changes from the respective groups,
    # such as create, update, and deletion of access rights
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_associated_roles()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._update_associated_roles()
        return res

    def unlink(self):
        if self.env.context.get("updating_role_model_access") or self.env.context.get(
            "install_mode"
        ):
            return super().unlink()
        roles = self._get_associated_roles()
        res = super().unlink()
        if roles:
            roles.with_context(
                updating_role_model_access=True
            )._update_role_model_access()
        return res

    def _get_associated_roles(self):
        """
        Find roles where the trans_implied_ids includes the group_ids
        of the current model access records.
        """
        group_ids = self.mapped("group_id").ids
        if not group_ids:
            return False
        roles = self.env["res.users.role"].search([])
        return roles.filtered(
            lambda r: not set(r.trans_implied_ids.ids).isdisjoint(group_ids)
        )

    def _update_associated_roles(self):
        if self.env.context.get("updating_role_model_access") or self.env.context.get(
            "install_mode"
        ):
            return
        roles = self._get_associated_roles()
        if roles:
            roles.with_context(
                updating_role_model_access=True
            )._update_role_model_access()
