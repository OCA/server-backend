# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

DEFAULT_PERM_FIELDS = {
    "perm_read": False,
    "perm_write": False,
    "perm_create": False,
    "perm_unlink": False,
}


class ResUsersRole(models.Model):
    _name = "res.users.role"
    _inherit = ["res.users.role"]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_role_model_access()
        return records

    def unlink(self):
        recs = (
            self.sudo()
            if self._bypass_rules() or self.env.user.bypass_role_policy
            else self
        )
        return super(ResUsersRole, recs).unlink()

    def write(self, vals):
        update_access = "implied_ids" in vals
        res = super().write(vals)
        if update_access:
            self._update_role_model_access()
        return res

    def _update_role_model_access(self, perm_fields=None):
        """
        Synchronize the access rights from the associated user groups
        into the role's model access records.
        """
        all_perm_fields = self.collect_all_perm_fields(perm_fields)

        # Precompute the trans_implied_ids before clearing the ORM cache
        precomputed_groups = {role.id: role.sudo().trans_implied_ids for role in self}

        self.invalidate_recordset(["implied_ids"])
        self.mapped("group_id").invalidate_recordset(["implied_ids"])
        ir_access_vals = []
        for role in self:
            role._clear_existing_model_access()

            # Inject the precomputed groups into the context to skip re-computation
            role_ctx = role.with_context(
                precomputed_role_groups=precomputed_groups[role.id]
            )
            access_records = role_ctx.model_access_ids
            model_permissions = self.parse_model_access(
                access_records, perm_fields=all_perm_fields
            )

            ir_access_vals += role._prepare_model_access_vals(model_permissions)
        if ir_access_vals:
            self.env["ir.model.access"].with_context(
                updating_role_model_access=True
            ).create(ir_access_vals)

    def collect_all_perm_fields(self, perm_fields=None):
        return DEFAULT_PERM_FIELDS | (perm_fields or {})

    @api.depends("implied_ids", "implied_ids.model_access")
    def _compute_model_access_ids(self):
        for rec in self:
            rec.model_access_ids = rec._get_implied_model_access_records()
            rec.model_access_count = len(rec.model_access_ids)

    def _get_implied_model_access_records(self):
        self.ensure_one()
        precomputed_role_groups = self.env.context.get("precomputed_role_groups")
        if precomputed_role_groups is not None:
            return precomputed_role_groups.mapped("model_access")
        return self.sudo().trans_implied_ids.model_access

    def _clear_existing_model_access(self):
        self.ensure_one()
        self.env["ir.model.access"].with_context(
            updating_role_model_access=True
        ).search([("group_id", "=", self.group_id.id)]).unlink()

    def _prepare_model_access_vals(self, model_permissions):
        self.ensure_one()
        return [
            {
                "name": model_rec.model,
                "model_id": model_rec.id,
                "group_id": self.group_id.id,
                **perms,
            }
            for model_rec, perms in model_permissions.items()
        ]

    def parse_model_access(self, model_access, perm_fields):
        """Aggregate permission fields per model, OR-ing flags across access records."""
        model_permissions = {}
        for access in model_access:
            perms = model_permissions.setdefault(access.model_id, perm_fields.copy())
            for field_name in perm_fields:
                perms[field_name] |= getattr(access, field_name)
        return model_permissions


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    def unlink(self):
        recs = (
            self.sudo()
            if self.role_id._bypass_rules() or self.env.user.bypass_role_policy
            else self
        )
        return super(ResUsersRoleLine, recs).unlink()
