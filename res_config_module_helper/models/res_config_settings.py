# -*- coding: utf-8 -*-
# 2019 initOS (Amjad Enaya <amjad.enaya@initos.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.multi
    def execute_from_confirm_wiz(self):
        self.ensure_one()
        res = super(ResConfigSettings, self).execute()
        return res

    @api.multi
    def execute(self):
        self.ensure_one()
        ModuleSudo = self.env['ir.module.module'].sudo()
        module_fields = filter(lambda x: x.startswith('module_'), self._fields.keys())
        module_names = list(map(lambda x: x.replace("module_", ''), module_fields))
        modules = ModuleSudo.search(
            [('name', 'in', module_names),
             ('state', 'in', ['to install', 'installed', 'to upgrade'])
             ])
        need_warning = False
        for obj in modules:
            field_name = 'module_' + obj.name
            if not self[field_name]:
                need_warning = True
                break
        if need_warning:
            print('warning needed')
            dic = {
                'type': 'ir.actions.act_window',
                'name': 'Confirmation',
                'res_model': 'confirm.uninstall',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': False,
                'view_id': self.env.ref('res_config_module_helper.confirm_uninstall_form', False).id,
                'target': 'new',
                'context': {'default_res_id': self.id}
            }
            return dic
        else:
            res = super(ResConfigSettings, self).execute()
            return res

