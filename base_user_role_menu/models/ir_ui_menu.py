# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    role_ids = fields.Many2many(
        comodel_name="res.users.role",
        string="Roles with Access",
        compute="_compute_role_ids",
        search="_search_role_ids",
    )
    has_no_role = fields.Boolean(
        string="No Role Restriction",
        compute="_compute_role_ids",
        search="_search_has_no_role",
    )

    def _compute_role_ids(self):
        all_roles = self.env["res.users.role"].search([])
        group_to_roles = {}
        for role in all_roles:
            implied_groups = role.group_id | role.group_id.trans_implied_ids
            for grp in implied_groups:
                group_to_roles.setdefault(grp.id, self.env["res.users.role"])
                group_to_roles[grp.id] |= role

        for menu in self:
            if not menu.groups_id:
                menu.role_ids = self.env["res.users.role"]
                menu.has_no_role = True
                continue

            roles = self.env["res.users.role"]
            for grp in menu.groups_id:
                roles |= group_to_roles.get(grp.id, self.env["res.users.role"])

            menu.role_ids = roles
            menu.has_no_role = not bool(roles)

    def _search_role_ids(self, operator, value):
        if operator not in ("in", "not in", "=", "!="):
            return []

        roles = self.env["res.users.role"]
        if isinstance(value, (list, tuple)):
            roles = roles.browse(value)
        elif isinstance(value, int):
            roles = roles.browse([value])

        group_ids = []
        for role in roles:
            implied = role.group_id | role.group_id.trans_implied_ids
            group_ids.extend(implied.ids)
        menus = self.env["ir.ui.menu"].search([("groups_id", "in", group_ids)])
        if operator in ("in", "="):
            return [("id", "in", menus.ids)]
        else:
            return [("id", "not in", menus.ids)]

    def _search_has_no_role(self, operator, value):
        if operator not in ("=", "!="):
            return []
        menus_with_roles = self.env["ir.ui.menu"].search([("groups_id", "!=", False)])
        if (operator == "=" and value) or (operator == "!=" and not value):
            return [("id", "not in", menus_with_roles.ids)]
        else:
            return [("id", "in", menus_with_roles.ids)]
