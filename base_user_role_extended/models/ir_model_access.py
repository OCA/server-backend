# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools

class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    @api.model
    @tools.ormcache('uid')
    def _get_role_model_permission_map(self, uid):
        user = self.env['res.users'].sudo().browse(uid)
        roles = user.role_line_ids.filtered(lambda l: l.is_enabled).mapped('role_id')
        if not roles:
            return {}

        role_access_records = self.env['role.model.access'].sudo().search([
            ('role_id', 'in', roles.ids)
        ])
        
        permission_map = {}
        for record in role_access_records:
            model_name = record.model_id.model
            if model_name not in permission_map:
                permission_map[model_name] = {
                    'read': False, 'write': False, 'create': False, 'unlink': False
                }
            
            permission_map[model_name]['read'] = permission_map[model_name]['read'] or record.perm_read
            permission_map[model_name]['write'] = permission_map[model_name]['write'] or record.perm_write
            permission_map[model_name]['create'] = permission_map[model_name]['create'] or record.perm_create
            permission_map[model_name]['unlink'] = permission_map[model_name]['unlink'] or record.perm_unlink
            
        return permission_map

    @api.model
    @tools.ormcache('self.env.uid', 'mode')
    def _get_allowed_models(self, mode='read'):
        if self.env.su:
            return super()._get_allowed_models(mode)

        allowed_models = set(super()._get_allowed_models(mode))

        permission_map = self._get_role_model_permission_map(self.env.uid)
        if not permission_map:
            return frozenset(allowed_models)

        for model_name, overrides in permission_map.items():
            if overrides.get(mode, False):
                allowed_models.add(model_name)
            else:
                allowed_models.discard(model_name)

        return frozenset(allowed_models)
