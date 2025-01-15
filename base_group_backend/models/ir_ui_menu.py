# Copyright 2024 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    @api.returns("self")
    def get_user_roots(self):
        """Avoid to display root menus with no defined groups_id to Backend UI Users
        like 'spreadsheet_dashboard.spreadsheet_dashboard_menu_root'
        or 'base.menu_management'.

        """
        res = super().get_user_roots()
        if self.env.user.has_group("base_group_backend.group_backend_ui_users"):
            return res.filtered(lambda m: m.groups_id)
        else:
            return res
