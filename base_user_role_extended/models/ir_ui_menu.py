# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools
from odoo.tools import config


class IrUiMenu(models.Model):
    _name = "ir.ui.menu"
    _inherit = ["ir.ui.menu", "role.policy.menu.action.common"]

    role_ids = fields.Many2many(
        comodel_name="res.users.role",
        relation="res_role_menu_rel",
        column1="menu_id",
        column2="role_id",
        string="Roles",
    )

    @api.model
    @tools.ormcache("frozenset(self.env.user.groups_id.ids)", "debug")
    def _visible_menu_ids(self, debug=False):
        """
        Hide all menus without the role_group(s) of the user.
        """
        if self.env.user.bypass_role_policy or config.get("test_enable"):
            return self._visible_menu_ids_user_admin(debug=debug)

        visible_ids = super()._visible_menu_ids(debug=debug)
        # role_line_ids.role_id gives the actual res.users.role records
        user_roles = self.env.user.role_line_ids.filtered(
            lambda lines: lines.is_enabled
        ).mapped("role_id")
        user_groups = user_roles.mapped("group_id")
        for group_ref in self._role_policy_untouchable_groups():
            user_groups |= self.env.ref(group_ref)

        menus = self.browse()
        for menu in self.browse(visible_ids):
            if menu.groups_id & user_groups:
                menus |= menu

        # keep only action menus and their folder ancestors
        action_menus = menus.filtered(lambda m: m.action and m.action.exists())

        def collect_parent_ids(menu, ids):
            parent = menu.parent_id
            if parent and parent in menus:
                ids.append(parent.id)
                collect_parent_ids(parent, ids)

        filtered_ids = []
        for menu in action_menus:
            ids = [menu.id]
            collect_parent_ids(menu, ids)
            filtered_ids.extend(ids)

        return set(filtered_ids)

    @api.model
    @tools.ormcache("frozenset(self.env.user.groups_id.ids)", "debug")
    def _visible_menu_ids_user_admin(self, debug=False):
        """
        Same logic as in base/models/ir_ui_menu.py but we ignore
        the role groups for user_root and user_admin.
        """
        # retrieve all menus, and determine which ones are visible
        context = {"ir.ui.menu.full_list": True}
        menus = self.with_context(**context).search([])

        groups = self.env.user.groups_id
        if not debug:
            groups = groups - self.env.ref("base.group_no_one")
        # first discard all menus with groups the user does not have
        menus = menus.filtered(
            lambda menu: not menu.groups_id.filtered(lambda r: not r.role)
            or menu.groups_id & groups
        )

        # take apart menus that have an action
        action_menus = menus.filtered(lambda m: m.action and m.action.exists())
        folder_menus = menus - action_menus
        visible = self.browse()

        # process action menus, check whether their action is allowed
        access = self.env["ir.model.access"]
        MODEL_GETTER = {
            "ir.actions.act_window": lambda action: action.res_model,
            "ir.actions.report": lambda action: action.model,
            "ir.actions.server": lambda action: action.model_id.model,
        }
        for menu in action_menus:
            get_model = MODEL_GETTER.get(menu.action._name)
            if (
                not get_model
                or not get_model(menu.action)
                or access.check(get_model(menu.action), "read", False)
            ):
                # make menu visible, and its folder ancestors, too
                visible += menu
                menu = menu.parent_id
                while menu and menu in folder_menus and menu not in visible:
                    visible += menu
                    menu = menu.parent_id

        return set(visible.ids)
