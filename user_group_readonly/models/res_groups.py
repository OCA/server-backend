# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import _, models


class ResGroups(models.Model):
    _inherit = "res.groups"

    def action_user_group_readonly(self):
        """Assign read permissions to all models, menus, actions"""
        self.ensure_one()
        for model in ('ir.ui.menu', 'ir.actions.act_window'):
            to_add = self.env[model].browse([])
            to_remove = self.env[model].browse([])
            for record in self.env[model].search([('groups_id', '!=', False)]):
                if record.groups_id == self:
                    to_remove += record
                elif self not in record.groups_id:
                    to_add += record
            to_add.write({'groups_id': [(4, self.id)]})
            to_remove.write({'groups_id': [(3, self.id)]})

        for model in self.env['ir.model'].search([('transient', '=', False)]):
            vals = {}
            if not model.access_ids.filtered(lambda x: x.group_id == self):
                vals['access_ids'] = [(0, 0, {
                    'group_id': self.id, 'perm_read': True,
                    'name': _('Access %(name)s') % model,
                })]
            model.write(vals)
