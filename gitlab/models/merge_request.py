from odoo import api, fields, models

from ..utils import _gitlab_datetime_to_odoo


class MergeRequest(models.Model):
    _name = "gitlab.merge.request"
    _description = "Gitlab Merge Request"

    project_id = fields.Many2one(
        comodel_name="gitlab.project", string="Project", required=True
    )
    gitlab_id = fields.Many2one(
        comodel_name="gitlab", string="Gitlab", related="project_id.gitlab_id"
    )
    external_id = fields.Char(string="External ID", required=True)
    name = fields.Char(required=True)
    description = fields.Text()
    url = fields.Char(required=True)
    created_at = fields.Datetime()
    updated_at = fields.Datetime()
    closed_at = fields.Datetime()
    merged_at = fields.Datetime()
    author_username = fields.Char(string="Username")
    state = fields.Selection(
        selection=[
            ("opened", "Opened"),
            ("closed", "Closed"),
            ("merged", "Merged"),
            ("locked", "Locked"),
        ]
    )
    note_ids = fields.One2many(
        comodel_name="gitlab.note",
        inverse_name="merge_request_id",
        string="Notes",
    )
    approval_ids = fields.One2many(
        comodel_name="gitlab.merge.request.approval",
        inverse_name="merge_request_id",
        string="Approvals",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Author Partner",
        compute="_compute_partner_id",
        store=True,
    )
    throughtput_time = fields.Integer(
        string="Throughput Time (days)", compute="_compute_throughtput_time", store=True
    )

    _sql_constraints = [
        (
            "gitlab_merge_request_uniq",
            "unique(project_id, external_id)",
            "A merge request with the same External "
            "ID already exists for this project.",
        ),
    ]

    @api.depends("created_at", "merged_at", "closed_at")
    def _compute_throughtput_time(self):
        for merge_request in self:
            if merge_request.merged_at and merge_request.created_at:
                delta = merge_request.merged_at - merge_request.created_at
                merge_request.throughtput_time = delta.days
            if merge_request.closed_at and merge_request.created_at:
                delta = merge_request.closed_at - merge_request.created_at
                merge_request.throughtput_time = delta.days
            else:
                delta = fields.Datetime.now() - merge_request.created_at
                merge_request.throughtput_time = delta.days

    @api.depends("author_username")
    def _compute_partner_id(self):
        for merge_request in self:
            partner_id = self.env["res.partner"].get_by_gitlab_username(
                merge_request.author_username
            )
            merge_request.partner_id = partner_id

    def reconcile_partner(self):
        self._compute_partner_id()

    def import_approvals(self):
        for merge_request in self:
            merge_request.with_delay(max_retries=0)._import_approvals()

    def _import_approvals(self):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        project = conn.projects.get(self.project_id.external_id, max_retries=-1)
        merge_request = project.mergerequests.get(self.external_id, max_retries=-1)
        approvals = merge_request.approvals.get(max_retries=-1)
        create_values = []
        for approval in approvals.approved_by:
            approval_user_id = str(approval["user"]["id"])
            if self.approval_ids.filtered(
                lambda a, iid=approval_user_id: a.approver_id == iid
            ):
                continue
            create_values.append(
                {
                    "merge_request_id": self.id,
                    "approver_username": approval["user"]["username"],
                    "approver_id": approval_user_id,
                    "approved_at": _gitlab_datetime_to_odoo(approval["approved_at"]),
                }
            )
        self.env["gitlab.merge.request.approval"].create(create_values)

    def import_notes(self):
        for merge_request in self:
            merge_request.with_delay(max_retries=0)._import_notes(
                1, merge_request.gitlab_id.per_page
            )

    def _import_notes(self, page, per_page):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        project = conn.projects.get(self.project_id.external_id, max_retries=-1)
        merge_request = project.mergerequests.get(self.external_id, max_retries=-1)
        params = {
            "page": page,
            "per_page": per_page,
            "sort": "asc",
            "order_by": "created_at",
        }
        notes = merge_request.notes.list(**params)
        existing_notes = self.note_ids.mapped("external_id")
        filtered_notes = filter(lambda n: str(n.id) not in existing_notes, notes)
        create_values = [
            {
                "project_id": self.project_id.id,
                "external_id": str(note.id),
                "name": note.body,
                "created_at": _gitlab_datetime_to_odoo(note.created_at),
                "author_username": note.author["username"],
                "merge_request_id": self.id,
                "url": f"{self.url}#note_{note.id}",
            }
            for note in filtered_notes
        ]
        self.env["gitlab.note"].create(create_values)
        if not notes:
            return
        self._import_notes(page + 1, per_page)
