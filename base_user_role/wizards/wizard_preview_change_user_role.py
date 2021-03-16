# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WizardPreviewChangeUserRole(models.TransientModel):
    _name = "wizard.preview.change.user.role"
    _description = "Wizard Preview Change user Roles"

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda x: x._default_user_id(),
    )

    role_ids = fields.Many2many(
        comodel_name="res.users.role"
    )

    hide_role_groups = fields.Boolean(
        string="Hide Role Groups",
        default=True,
        help="If checked, the preview will exclude groups that are related"
        " to roles."
    )

    added_group_ids = fields.Many2many(
        comodel_name="res.groups",
        compute="_compute_added_removed_group_ids",
        store=False,
        string="Groups to Add",
        help="New groups that will be added, when applying role changes",
    )

    removed_group_ids = fields.Many2many(
        comodel_name="res.groups",
        compute="_compute_added_removed_group_ids",
        store=False,
        string="Groups to Remove",
        help="Obsolete groups that will be removed, when applying role"
        " changes",
    )

    def _default_user_id(self):
        return self._context.get('active_id', False)

    @api.multi
    @api.depends("role_ids", "user_id", "hide_role_groups")
    def _compute_added_removed_group_ids(self):
        for wizard in self:
            hidden_group_ids = []
            if wizard.hide_role_groups:
                all_roles = self.env["res.users.role"].search([])
                hidden_group_ids = all_roles.mapped("group_id").ids

            new_group_ids = list(
                set(
                    wizard.mapped("role_ids.group_id").ids
                    + wizard.mapped("role_ids.implied_ids").ids
                    + wizard.mapped("role_ids.trans_implied_ids").ids
                )
            )
            current_group_ids = wizard.user_id.groups_id.ids
            wizard.added_group_ids = list(
                set(new_group_ids) - set(current_group_ids)
                - set(hidden_group_ids))
            wizard.removed_group_ids = list(
                set(current_group_ids) - set(new_group_ids)
                - set(hidden_group_ids))

    def apply(self):
        for wizard in self:
            line_vals = [[5]]
            line_vals += [
                [
                    0, 0, {
                        "role_id": role.id,
                    }
                ] for role in wizard.role_ids
            ]
            wizard.user_id.write({"role_line_ids": line_vals})
