from odoo import api, fields, models


class MergeRequestApproval(models.Model):
    _name = "gitlab.merge.request.approval"
    _description = "Gitlab Merge Request Approval"

    merge_request_id = fields.Many2one(
        comodel_name="gitlab.merge.request",
        string="Merge Request",
        required=True,
        ondelete="cascade",
    )
    approver_username = fields.Char(required=True)
    approver_id = fields.Char(string="Approver ID", required=True)
    approved_at = fields.Datetime(required=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Approver Partner",
        compute="_compute_partner_id",
        store=True,
    )

    @api.depends("approver_username")
    def _compute_partner_id(self):
        for approval in self:
            partner_id = self.env["res.partner"].get_by_gitlab_username(
                approval.approver_username
            )
            approval.partner_id = partner_id

    def reconcile_partner(self):
        self._compute_partner_id()
