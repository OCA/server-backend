from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from ..utils import _gitlab_datetime_to_odoo


class Issue(models.Model):
    _name = "gitlab.issue"
    _description = "Gitlab Issue"

    project_id = fields.Many2one(
        comodel_name="gitlab.project", string="Project", required=True
    )
    gitlab_id = fields.Many2one(
        comodel_name="gitlab", string="Gitlab", related="project_id.gitlab_id"
    )
    external_id = fields.Char(string="External ID", required=True)
    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    url = fields.Char(required=True)
    created_at = fields.Datetime()
    updated_at = fields.Datetime()
    closed_at = fields.Datetime()
    author_username = fields.Char(string="Username")
    state = fields.Selection(
        selection=[
            ("opened", "Opened"),
            ("closed", "Closed"),
        ]
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

    @api.depends("created_at", "closed_at")
    def _compute_throughtput_time(self):
        for issue in self:
            if issue.closed_at and issue.created_at:
                delta = issue.closed_at - issue.created_at
                issue.throughtput_time = delta.days
            else:
                delta = fields.Datetime.now() - issue.created_at
                issue.throughtput_time = delta.days

    @api.depends("author_username")
    def _compute_partner_id(self):
        for issue in self:
            partner_id = self.env["res.partner"].get_by_gitlab_username(
                issue.author_username
            )
            issue.partner_id = partner_id

    def reconcile_partner(self):
        self._compute_partner_id()

    _sql_constraints = [
        (
            "unique_issue_per_project",
            "unique(project_id, external_id)",
            "The issue must be unique per project.",
        ),
    ]

    note_ids = fields.One2many(
        comodel_name="gitlab.note",
        inverse_name="issue_id",
        string="Notes",
    )

    def import_notes(self):
        until = fields.Datetime.now()

        for issue in self:
            since = datetime.min
            last_note = self.env["gitlab.note"].search(
                [("issue_id", "=", issue.id)],
                order="created_at desc",
                limit=1,
            )
            if last_note:
                since = last_note.created_at
                # Adding a second to avoid duplicate notes on the boundary
                since += relativedelta(seconds=1)

            issue.with_delay(max_retries=0)._import_notes(
                1, issue.gitlab_id.per_page, since, until
            )

    def _import_notes(self, page, per_page, since, until):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        project = conn.projects.get(self.project_id.external_id, max_retries=-1)
        issue = project.issues.get(self.external_id, max_retries=-1)
        params = {
            "page": page,
            "per_page": per_page,
            "sort": "asc",
            "order_by": "created_at",
        }
        notes = issue.notes.list(**params)
        existing_notes = self.note_ids.mapped("external_id")
        filtered_notes = filter(lambda n: str(n.id) not in existing_notes, notes)
        create_values = [
            {
                "project_id": self.project_id.id,
                "external_id": str(note.id),
                "name": note.body,
                "created_at": _gitlab_datetime_to_odoo(note.created_at),
                "author_username": note.author["username"],
                "issue_id": self.id,
                "url": f"{self.url}#note_{note.id}",
            }
            for note in filtered_notes
        ]
        self.env["gitlab.note"].create(create_values)
        if not notes:
            return
        self._import_notes(page + 1, per_page, since, until)
