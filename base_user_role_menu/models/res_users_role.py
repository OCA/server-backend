# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    menu_ids = fields.Many2many(
        comodel_name="ir.ui.menu",
        string="Accessible Menus",
        compute="_compute_menu_ids",
        help="All menus accessible through this role.",
    )
    menu_count = fields.Integer(
        string="Menu Count",
        compute="_compute_menu_ids",
    )

    def _compute_menu_ids(self):
        for role in self:
            implied_groups = role.group_id | role.group_id.trans_implied_ids
            menus = self.env["ir.ui.menu"].search([])
            filtered_menus = menus.filtered(
                lambda menu: any(group in menu.groups_id for group in implied_groups)
            )
            role.menu_ids = filtered_menus
            role.menu_count = len(filtered_menus)

    def action_view_menus(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Menus — %s" % self.name,
            "res_model": "ir.ui.menu",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.menu_ids.ids)],
            "context": {"default_role_id": self.id},
        }
