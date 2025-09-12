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
        default_user = self.env.ref("base.default_user", raise_if_not_found=False)
        default_values = []
        if default_user:
            for role_line in default_user.with_context(active_test=False).role_line_ids:
                default_values.append(
                    {
                        "role_id": role_line.role_id.id,
                        "date_from": role_line.date_from,
                        "date_to": role_line.date_to,
                        "is_enabled": role_line.is_enabled,
                    }
                )
        return default_values

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

    @api.model
    def _get_self_writable_groups(self):
        group = self.env.ref(
            "mail.group_mail_notification_type_inbox", raise_if_not_found=False
        )
        return group or self.env["res.groups"]

    def set_groups_from_roles(self, force=False):
        """Set (replace) the groups following the roles defined on users.
        If no role is defined on the user, its groups are let untouched unless
        the `force` parameter is `True`.
        """
        role_groups = {}
        # We obtain all the groups associated to each role first, so that
        # it is faster to compare later with each user's groups.
        for role in self.mapped("role_line_ids.role_id"):
            role_groups[role] = list(
                set(
                    role.group_id.ids
                    + role.implied_ids.ids
                    + role.trans_implied_ids.ids
                )
            )
        self_writable_group_ids = self._get_self_writable_groups().ids
        for user in self:
            if not user.role_line_ids and not force:
                continue
            user_group_ids = set(user.groups_id.ids).difference(self_writable_group_ids)
            group_ids = set()
            for role_line in user._get_enabled_roles():
                role = role_line.role_id
                group_ids.update(role_groups[role])
            groups_to_add = group_ids - user_group_ids
            groups_to_remove = user_group_ids - group_ids
            to_add = [(4, gr) for gr in groups_to_add]
            to_remove = [(3, gr) for gr in groups_to_remove]
            groups = to_remove + to_add
            if groups:
                vals = {"groups_id": groups}
                super(ResUsers, user).write(vals)
        return True
