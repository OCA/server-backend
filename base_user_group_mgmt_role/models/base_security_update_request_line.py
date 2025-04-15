# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models


class BaseSecurityUpdateLine(models.Model):

    _inherit = "base.security.update.request.line"

    action = fields.Selection(
        default="user_add_role",
    )
    role_ids = fields.Many2many(
        comodel_name="res.users.role",
        string="Roles",
    )
    is_role_ids_visible = fields.Boolean(
        compute="_compute_is_role_ids_visible",
    )
    role_date_from = fields.Date()
    role_date_to = fields.Date()
    is_role_edit_data_visible = fields.Boolean(
        compute="_compute_is_role_edit_data_visible",
    )

    @api.depends("role_ids")
    def _compute_name(self):
        return super()._compute_name()

    @api.depends(
        "action",
    )
    def _compute_is_role_ids_visible(self):
        for rec in self:
            rec.is_role_ids_visible = "role" in rec.action

    @api.depends(
        "action",
    )
    def _compute_is_role_edit_data_visible(self):
        for rec in self:
            rec.is_role_edit_data_visible = rec.action in (
                "user_role_edit",
                "user_add_role",
            )

    @api.model
    def _selection_action(self):
        return [
            ("user_add_role", _("Add a role to a user")),
            ("user_remove_role", _("Remove a role from a user")),
            ("user_role_edit", _("Update role of user")),
            ("role_add_group", _("Add a group to a role")),
            ("role_remove_group", _("Remove a group from a role")),
            *super()._selection_action(),
        ]

    def _get_name(self):
        self.ensure_one()
        action = self.action
        groups = ", ".join(self.group_1_ids.mapped("display_name")) or _("Groups 1")
        roles = ", ".join(self.role_ids.mapped("display_name")) or _("Roles")
        users = ", ".join(self.user_ids.mapped("display_name")) or _("Users")
        if action == "user_add_role":
            return _(
                "Add role(s) '%(roles)s' to user(s) '%(users)s'",
                roles=roles,
                users=users,
            )
        elif action == "user_remove_role":
            return _(
                "Remove role(s) '%(roles)s' from user(s) '%(users)s'",
                roles=roles,
                users=users,
            )
        elif action == "role_add_group":
            return _(
                "Add group(s) '%(groups)s' to role(s) '%(roles)s'",
                groups=groups,
                roles=roles,
            )
        elif action == "role_remove_group":
            return _(
                "Remove group(s) '%(groups)s' from role(s) '%(roles)s'",
                groups=groups,
                roles=roles,
            )
        elif action == "user_role_edit":
            return _(
                "Update role(s) '%(roles)s' of user(s) '%(users)s'",
                roles=roles,
                users=users,
            )
        return super()._get_name()

    def _get_role_line_values(self, role, user):
        self.ensure_one()
        return {
            "user_id": user.id,
            "role_id": role.id,
            "date_from": self.role_date_from,
            "date_to": self.role_date_to,
        }

    def _get_existing_role_line_domain(self, role, user):
        self.ensure_one()
        return [
            ("role_id", "=", role.id),
            ("user_id", "=", user.id),
        ]

    def _get_existing_role_line(self, role, user):
        self.ensure_one()
        return (
            self.env["res.users.role.line"]
            .with_context(active_test=False)
            .search(self._get_existing_role_line_domain(role, user), limit=1)
        )

    def _do_update_user_add_role(self):
        self.ensure_one()
        self._check_can_process_do_update()
        for user in self.user_ids:
            for role in self.role_ids:
                line = self._get_existing_role_line(role, user)
                values = self._get_role_line_values(role, user)
                if line:
                    line.write(values)
                    continue
                user.write(
                    {
                        "role_line_ids": [
                            Command.create(values),
                        ]
                    }
                )

    def _do_update_user_remove_role(self):
        self.ensure_one()
        self._check_can_process_do_update()
        for user in self.user_ids:
            for role in self.role_ids:
                line = self._get_existing_role_line(role, user)
                line.unlink()

    def _do_update_user_role_edit(self):
        self.ensure_one()
        return self._do_update_user_add_role()

    def _do_update_role_add_group(self):
        self.ensure_one()
        self._check_can_process_do_update()
        self.role_ids.write(
            {"implied_ids": [Command.link(group.id) for group in self.group_1_ids]}
        )

    def _do_update_role_remove_group(self):
        self.ensure_one()
        self._check_can_process_do_update()
        self.role_ids.write(
            {"implied_ids": [Command.unlink(group.id) for group in self.group_1_ids]}
        )
