# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResRole(models.Model):
    _name = "res.users.role"
    _inherit = ["res.users.role", "mail.thread"]

    menu_ids = fields.Many2many(
        comodel_name="ir.ui.menu",
        relation="res_role_menu_rel",
        column1="role_id",
        column2="menu_id",
        string="Menu Items",
    )

    def _init_restore_role_groups(self):
        """Re-add the role's group to any menu that is missing it."""
        roles = self.with_context(
            **dict(self.env.context, role_policy_init=True, active_test=False)
        ).search([])
        for role in roles:
            menus_missing_group = role.menu_ids.filtered(
                lambda m, r=role: r.group_id not in m.groups_id
            )
            for menu in menus_missing_group:
                menu.write({"groups_id": [(4, role.group_id.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        """
        Delegate to super (which handles group creation via _inherits).
        After creation, sync the role group to any assigned menu items
        and ensure the role group is marked as a role.
        """
        self = self.with_context(**dict(self.env.context, role_policy_init=True))
        # Ensure the group created by _inherits has role=True
        for vals in vals_list:
            vals["role"] = True

        new_roles = super().create(vals_list)
        for role, vals in zip(new_roles, vals_list, strict=False):
            if vals.get("menu_ids"):
                role.menu_ids.write({"groups_id": [(4, role.group_id.id)]})
        return new_roles

    def write(self, vals):
        self = self.with_context(**dict(self.env.context, role_policy_init=True))
        # Collect menu group updates before writing so we can diff old vs new
        updates = []
        for role in self:
            if "menu_ids" in vals:
                role_gid = role.group_id.id
                model = self._fields["menu_ids"].comodel_name
                for entry in vals["menu_ids"]:
                    if entry[0] == 6:
                        # Replace — compute the diff
                        old_ids = set(role.menu_ids.ids)
                        new_ids = set(entry[2])
                        removal_ids = old_ids - new_ids
                        addition_ids = new_ids - old_ids
                        if removal_ids:
                            updates.append((model, removal_ids, [(3, role_gid)]))
                        if addition_ids:
                            updates.append((model, addition_ids, [(4, role_gid)]))
                    elif entry[0] in (3, 4):
                        updates.append((model, [entry[1]], [(entry[0], role_gid)]))
                    elif entry[0] == 5:
                        removal_ids = set(role.menu_ids.ids)
                        if removal_ids:
                            updates.append((model, removal_ids, [(3, role_gid)]))
                    else:
                        raise NotImplementedError(
                            f"Unsupported x2many command {entry[0]} for menu_ids"
                        )
        res = super().write(vals)
        for model_name, model_ids, command in updates:
            self.env[model_name].browse(model_ids).write({"groups_id": command})
        return res
