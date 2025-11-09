# Copyright 2014 ABF OSIELL <http://osiell.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    role_line_ids = fields.One2many(
        comodel_name="res.users.role.line",
        inverse_name="user_id",
        string="Role lines",
        default=lambda self: self._default_role_lines(),
        groups="base.group_erp_manager",
    )

    show_alert = fields.Boolean(compute="_compute_show_alert")

    @api.depends("role_line_ids")
    def _compute_show_alert(self):
        for user in self:
            user.show_alert = user.role_line_ids.filtered(lambda rec: rec.is_enabled)

    role_ids = fields.One2many(
        comodel_name="res.users.role",
        string="User Roles",
        compute="_compute_role_ids",
        compute_sudo=True,
        groups="base.group_erp_manager",
    )

    @api.model
    def _default_role_lines(self):
        """Default role lines for a new user.

        In Odoo 19, the former ``base.default_user`` template was removed in
        favor of a default group. There is no default user anymore to copy
        role lines from. Use a boolean on roles to mark the ones that should
        apply to new users.
        """
        default_roles = self.env["res.users.role"].search([("is_default", "=", True)])
        return [{"role_id": r.id} for r in default_roles]

    @api.depends("role_line_ids.role_id")
    def _compute_role_ids(self):
        for user in self:
            user.role_ids = user.role_line_ids.mapped("role_id")

    @api.model_create_multi
    def create(self, vals_list):
        new_records = super().create(vals_list)
        new_records.set_groups_from_roles()
        return new_records

    def write(self, vals):
        res = super().write(vals)
        self.sudo().set_groups_from_roles()
        return res

    def _get_enabled_roles(self):
        return self.role_line_ids.filtered(lambda rec: rec.is_enabled)

    def set_groups_from_roles(self, force=False):
        """Set (replace) the groups following the roles defined on users.
        If no role is defined on the user, its groups are let untouched unless
        the `force` parameter is `True`.
        """
        role_groups = {}
        # We obtain all the groups associated to each role first, so that
        # it is faster to compare later with each user's groups.
        for role in self.mapped("role_line_ids.role_id"):
            # v19: use transitive implied groups provided by ORM
            role_groups[role] = list(set(role.all_implied_ids.ids))
        for user in self:
            if not user.role_line_ids and not force:
                continue
            group_ids = []
            for role_line in user._get_enabled_roles():
                role = role_line.role_id
                group_ids += role_groups[role]
            group_ids = list(set(group_ids))  # Remove duplicates IDs
            # Preserve admin only if dropping it would leave zero administrators
            admin_group = self.env.ref("base.group_system", raise_if_not_found=False)
            if (
                admin_group
                and admin_group.id in user.group_ids.ids
                and admin_group.id not in group_ids
            ):
                other_admins = self.sudo().search_count(
                    [("id", "!=", user.id), ("group_ids", "in", admin_group.id)]
                )
                if other_admins == 0:
                    group_ids.append(admin_group.id)
            groups_to_add = list(set(group_ids) - set(user.group_ids.ids))
            groups_to_remove = list(set(user.group_ids.ids) - set(group_ids))
            to_add = [fields.Command.link(gr) for gr in groups_to_add]
            to_remove = [fields.Command.unlink(gr) for gr in groups_to_remove]
            groups = to_remove + to_add
            if groups:
                vals = {"group_ids": groups}
                super(ResUsers, user).write(vals)
        return True
