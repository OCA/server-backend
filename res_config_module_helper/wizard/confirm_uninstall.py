# -*- coding: utf-8 -*-
# 2019 initOS GmbH (Amjad Enaya <amjad.enaya@initos.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ConfirmUninstall(models.TransientModel):
    _name = 'confirm.uninstall'
    _description = 'Confirm before uninstall a module from config'

    def confirmed(self):
        self.ensure_one()
        res_id = int(self.env.context.get('default_res_id'))
        self.env["res.config.settings"].browse(res_id).execute_from_confirm_wiz()
        return

    def canceled(self):
        self.ensure_one()
        res_id = int(self.env.context.get('default_res_id'))
        return self.env["res.config.settings"].browse(res_id).cancel()


