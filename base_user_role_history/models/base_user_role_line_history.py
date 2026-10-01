# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BaseUserRoleLineHistory(models.Model):
    _name = "base.user.role.line.history"
    _description = "History of user roles"
    _order = "id desc"

    performed_action = fields.Selection(
        string="Action",
        selection=[("add", "Add"), ("unlink", "Delete"), ("edit", "Edit")],
        required=True,
    )
    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        ondelete="cascade",
        index=True,
    )
    old_role_id = fields.Many2one(
        string="Old role",
        comodel_name="res.users.role",
        ondelete="cascade",
        index=True,
    )
    new_role_id = fields.Many2one(
        string="New role",
        comodel_name="res.users.role",
        ondelete="cascade",
        index=True,
    )
    old_date_from = fields.Date(string="Old start date")
    new_date_from = fields.Date(string="New start date")
    old_date_to = fields.Date(string="Old end date")
    new_date_to = fields.Date(string="New end date")
    old_is_enabled = fields.Boolean(string="Active before edit")
    new_is_enabled = fields.Boolean(string="Active after edit")
