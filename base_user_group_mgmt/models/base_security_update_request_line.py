# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class BaseSecurityUpdateLine(models.Model):

    _name = "base.security.update.request.line"
    _description = "Base Security Update Line"

    request_id = fields.Many2one(
        comodel_name="base.security.update.request",
        string="Request",
        required=True,
        ondelete="cascade",
    )
    action = fields.Selection(
        selection="_selection_action",
        default="user_add_group",
        required=True,
    )
    name = fields.Char(
        compute="_compute_name",
        string="Description",
    )
    user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users",
    )
    is_user_ids_visible = fields.Boolean(
        compute="_compute_is_user_ids_visible",
    )
    group_1_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="security_req_line_group_1_rel",
        string="Groups 1",
    )
    is_group_1_ids_visible = fields.Boolean(
        compute="_compute_is_group_1_ids_visible",
    )
    group_2_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="security_req_line_group_2_rel",
        string="Groups 2",
    )
    is_group_2_ids_visible = fields.Boolean(
        compute="_compute_is_group_2_ids_visible",
    )
    state = fields.Selection(
        selection="_selection_state",
        default="to_do",
        readonly=True,
    )
    action_do_update_allowed = fields.Boolean(
        compute="_compute_action_do_update_allowed",
    )

    @api.depends(
        "action",
    )
    def _compute_is_user_ids_visible(self):
        for rec in self:
            rec.is_user_ids_visible = "user" in rec.action

    @api.depends("action")
    def _compute_is_group_1_ids_visible(self):
        for rec in self:
            rec.is_group_1_ids_visible = rec.action.count("group") > 0

    @api.depends("action")
    def _compute_is_group_2_ids_visible(self):
        for rec in self:
            rec.is_group_2_ids_visible = rec.action.count("group") > 1

    @api.depends("state", "request_id.state")
    def _compute_action_do_update_allowed(self):
        for rec in self:
            rec.action_do_update_allowed = (
                rec.state == "to_do" and rec.request_id.state == "approved"
            )

    @api.depends(
        "action",
        "user_ids",
        "group_1_ids",
        "group_2_ids",
    )
    def _compute_name(self):
        for rec in self:
            rec.name = rec._get_name()

    @api.model
    def _selection_action(self):
        return [
            ("user_add_group", _("Add a group to a user")),
            ("user_remove_group", _("Remove a group from a user")),
            ("group_add_group", _("Add a group to a group")),
            ("group_remove_group", _("Remove a group from a group")),
        ]

    @api.model
    def _selection_state(self):
        return [
            ("to_do", _("to Do")),
            ("done", _("Done")),
        ]

    def _get_name(self):
        self.ensure_one()
        action = self.action
        groups_1 = ", ".join(self.group_1_ids.mapped("display_name")) or _("Groups 1")
        groups_2 = ", ".join(self.group_2_ids.mapped("display_name")) or _("Groups 2")
        users = ", ".join(self.user_ids.mapped("display_name")) or _("Users")

        if action == "user_add_group":
            return _(
                "Add group(s) '%(groups_1)s' to user(s) '%(users)s'",
                groups_1=groups_1,
                users=users,
            )
        elif action == "user_remove_group":
            return _(
                "Remove group(s) '%(groups_1)s' from user(s) '%(users)s'",
                groups_1=groups_1,
                users=users,
            )
        elif action == "group_add_group":
            return _(
                "Add group(s) '%(groups_2)s' to group(s) '%(groups_1)s'",
                groups_2=groups_2,
                groups_1=groups_1,
            )
        elif action == "group_remove_group":
            return _(
                "Remove group(s) '%(groups_2)s' from group(s) '%(groups_1)s'",
                groups_2=groups_2,
                groups_1=groups_1,
            )
        return action

    def _do_updates(self):
        for rec in self:
            rec._do_update()

    def _do_update(self):
        self.ensure_one()
        method = getattr(self, "_do_update_%s" % self.action, None)
        if not method:
            raise UserError(_("Action has not been implemented yet."))
        res = method()
        self.write({"state": "done"})
        return res

    def _check_can_process_do_update(self):
        for rec in self:
            if not rec.action_do_update_allowed:
                raise UserError(
                    _(
                        "This action can't be processed. %(request)s, %(action)s",
                        request=rec.request_id.display_name,
                        action=rec.display_name,
                    )
                )

    def _do_update_user_add_group(self):
        self.ensure_one()
        self._check_can_process_do_update()
        self.user_ids.write(
            {"groups_id": [Command.link(group.id) for group in self.group_1_ids]}
        )

    def _do_update_user_remove_group(self):
        self.ensure_one()
        self._check_can_process_do_update()
        self.user_ids.write(
            {"groups_id": [Command.unlink(group.id) for group in self.group_1_ids]}
        )

    def _do_update_group_add_group(self):
        self.ensure_one()
        self._check_can_process_do_update()
        self.group_1_ids.write(
            {"implied_ids": [Command.link(group.id) for group in self.group_2_ids]}
        )

    def _do_update_group_remove_group(self):
        self.ensure_one()
        self._check_can_process_do_update()
        self.group_1_ids.write(
            {"implied_ids": [Command.unlink(group.id) for group in self.group_2_ids]}
        )
