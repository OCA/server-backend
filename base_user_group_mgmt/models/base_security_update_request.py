# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError

READONLY_STATES = {
    "draft": [("readonly", False)],
}


class BaseSecurityUpdateRequest(models.Model):

    _name = "base.security.update.request"
    _description = "Base Security Update"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    _mail_post_access = "read"
    _order = "date desc"

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user.id,
        readonly=True,
        states=READONLY_STATES,
    )
    date = fields.Datetime(
        default=lambda self: fields.Datetime.now(),
        copy=False,
        readonly=True,
        states=READONLY_STATES,
    )
    line_ids = fields.One2many(
        comodel_name="base.security.update.request.line",
        inverse_name="request_id",
        string="Lines",
        readonly=True,
        states=READONLY_STATES,
        copy=True,
    )
    state = fields.Selection(
        selection="_selection_state",
        default="draft",
        required=True,
        readonly=True,
        states=READONLY_STATES,
        copy=False,
        tracking=True,
    )
    approver_1_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approver 1",
        readonly=True,
        copy=False,
    )
    approver_2_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approver 2",
        readonly=True,
        copy=False,
    )
    action_confirm_allowed = fields.Boolean(
        compute="_compute_action_confirm_allowed",
    )
    action_first_approval_allowed = fields.Boolean(
        compute="_compute_action_first_approval_allowed",
    )
    action_second_approval_allowed = fields.Boolean(
        compute="_compute_action_second_approval_allowed",
    )
    action_reject_allowed = fields.Boolean(
        compute="_compute_action_reject_allowed",
    )

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, f"#{rec.id}"))
        return res

    def _compute_action_confirm_allowed(self):
        is_super_approver = self._is_user_super_approver()
        for rec in self:
            rec.action_confirm_allowed = rec.state == "draft" and (
                rec._is_user_request_creator() or is_super_approver
            )

    @api.depends_context("uid")
    @api.depends("user_id", "state")
    def _compute_action_first_approval_allowed(self):
        is_approver = self._is_user_approver()
        is_super_approver = self._is_user_super_approver()
        for rec in self:
            rec.action_first_approval_allowed = rec.state == "first_approval" and (
                (is_approver and not rec._is_user_request_creator())
                or is_super_approver
            )

    @api.depends_context("uid")
    @api.depends("approver_1_user_id", "user_id", "state")
    def _compute_action_second_approval_allowed(self):
        current_user = self.env.user
        is_approver = self._is_user_approver()
        is_manager = self._is_user_manager()
        for rec in self:
            rec.action_second_approval_allowed = rec.state == "second_approval" and (
                (
                    is_approver
                    and current_user != rec.approver_1_user_id
                    and not rec._is_user_request_creator()
                )
                or is_manager
            )

    @api.depends(
        "action_first_approval_allowed",
        "action_second_approval_allowed",
    )
    def _compute_action_reject_allowed(self):
        for rec in self:
            rec.action_reject_allowed = (
                rec.action_first_approval_allowed or rec.action_second_approval_allowed
            )

    @api.model
    def _selection_state(self):
        return [
            ("draft", _("Draft")),
            ("first_approval", _("1st Approval")),
            ("second_approval", _("2nd Approval")),
            ("approved", _("Approved")),
            ("rejected", _("Rejected")),
        ]

    @api.model
    def _is_user_super_approver(self):
        return self.env.user.has_group(
            "base_user_group_mgmt.security_management_super_approver"
        )

    @api.model
    def _is_user_approver(self):
        return self.env.user.has_group(
            "base_user_group_mgmt.security_management_approver"
        )

    @api.model
    def _is_user_manager(self):
        return self.env.user.has_group(
            "base_user_group_mgmt.security_management_manager"
        )

    def _is_user_request_creator(self):
        self.ensure_one()
        return self.env.user == self.user_id

    def _check_action_confirm_allowed(self):
        for rec in self:
            if not rec.action_confirm_allowed:
                raise UserError(
                    _("You can't confirm this request. %(name)s", name=rec.display_name)
                )

    def action_confirm(self):
        self.ensure_one()
        self._check_action_confirm_allowed()
        self.write({"state": "first_approval"})
        if self.action_first_approval_allowed:
            self.action_first_approval()

    def _check_action_first_approval_allowed(self):
        for rec in self:
            if not rec.action_first_approval_allowed:
                raise UserError(
                    _("You can't approve this request. %(name)s", name=rec.display_name)
                )

    def action_first_approval(self):
        self.ensure_one()
        self._check_action_first_approval_allowed()
        self.sudo().write(
            {
                "state": "second_approval",
                "approver_1_user_id": self.env.user.id,
            }
        )

    def _check_action_second_approval_allowed(self):
        for rec in self:
            if not rec.action_second_approval_allowed:
                raise UserError(
                    _("You can't approve this request. %(name)s", name=rec.display_name)
                )

    def action_second_approval(self):
        self.ensure_one()
        self._check_action_second_approval_allowed()
        self_sudo = self.sudo()
        self_sudo.write(
            {
                "state": "approved",
                "approver_2_user_id": self.env.user.id,
            }
        )
        self_sudo.with_user(SUPERUSER_ID).line_ids._do_updates()

    def _check_action_reject_allowed(self):
        for rec in self:
            if not rec.action_reject_allowed:
                raise UserError(
                    _("You can't reject this request. %(name)s", name=rec.display_name)
                )

    def action_reject(self):
        self.ensure_one()
        self._check_action_reject_allowed()
        self.sudo().write(
            {
                "state": "rejected",
                "approver_2_user_id": self.env.user.id,
            }
        )
