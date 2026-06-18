# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RoleModelAccess(models.Model):
    _name = "role.model.access"
    _description = "Role Model Access"

    role_id = fields.Many2one("res.users.role", string="Role", required=True, ondelete="cascade")
    model_id = fields.Many2one("ir.model", string="Model", required=True, ondelete="cascade")

    perm_read = fields.Boolean(string="Read", default=False)
    perm_write = fields.Boolean(string="Write", default=False)
    perm_create = fields.Boolean(string="Create", default=False)
    perm_unlink = fields.Boolean(string="Delete", default=False)

    _sql_constraints = [
        (
            "unique_role_model",
            "unique(role_id, model_id)",
            "A model can only be configured once per Role."
        )
    ]

    @api.constrains('role_id', 'model_id')
    def _check_unique_role_model(self):
        for record in self:
            if not record.role_id or not record.model_id:
                continue
            
            existing = self.search([
                ('role_id', '=', record.role_id.id),
                ('model_id', '=', record.model_id.id),
                ('id', '!=', record.id)
            ], limit=1)
            
            if existing:
                model_name = record.model_id.name or record.model_id.model
                raise ValidationError(_('The model "%s" is already configured for this Role.\n\nPlease edit the existing Model Access entry instead of creating a duplicate.') % model_name)

    def _clear_role_caches(self):
        self.env.registry.clear_cache()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._clear_role_caches()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._clear_role_caches()
        return res

    def unlink(self):
        self._clear_role_caches()
        return super().unlink()
