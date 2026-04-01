# Copyright (C) 2021 Daniel Reis
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class BaseModulePipInstall(models.TransientModel):
    _name = "base.module.pip.install"
    _description = "Pip Install Module"

    module_name = fields.Char()

    def action_module_open(self):
        return {
            "domain": [],  # TODO: filter by module name
            "name": "Modules",
            "view_mode": "tree,form",
            "res_model": "ir.module.module",
            "view_id": False,
            "type": "ir.actions.act_window",
        }

    def button_pip_install(self):
        Module = self.env["ir.module.module"]
        for wizard in self:
            Module.action_pip_install(wizard.module_name)
        # TODO: present output on form (mayve use states on wizard form)
        # TODO: update modules list
        # TODO: also install module_name?
        return self.action_module_open()
