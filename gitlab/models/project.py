from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models

from ..utils import _gitlab_datetime_to_odoo


class Project(models.Model):
    _name = "gitlab.project"
    _description = "Gitlab Project"

    gitlab_id = fields.Many2one(comodel_name="gitlab", string="Gitlab", required=True)
    name = fields.Char(required=True)
    external_id = fields.Char(string="External ID", store=True)
    url = fields.Char()
    group_id = fields.Many2one(
        comodel_name="gitlab.group",
        string="Group",
        required=True,
    )
    issue_ids = fields.One2many(
        comodel_name="gitlab.issue",
        inverse_name="project_id",
        string="Issues",
    )
    merge_request_ids = fields.One2many(
        comodel_name="gitlab.merge.request",
        inverse_name="project_id",
        string="Merge Requests",
    )

    def import_commits(self):
        until = fields.Datetime.now()

        for project in self:
            since = datetime.min
            last_commit = self.env["gitlab.commit"].search(
                [("project_id", "=", project.id)], order="committed_date desc", limit=1
            )
            if last_commit:
                since = last_commit.committed_date
                # Adding a second to avoid duplicate commits on the boundary
                since += relativedelta(seconds=1)

            project.with_delay(max_retries=0)._import_commits(
                1, project.gitlab_id.per_page, since, until
            )

    def _import_commits(self, page, per_page, since, until):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        project = conn.projects.get(self.external_id)
        params = {
            "page": page,
            "per_page": per_page,
            "until": fields.Datetime.to_string(until),
        }
        if since > datetime.min:
            params.update(since=fields.Datetime.to_string(since))
        commits = project.commits.list(**params)
        create_values = []
        for commit in commits:
            create_values.append(
                {
                    "project_id": self.id,
                    "author_email": commit.author_email,
                    "author_name": commit.author_name,
                    "external_id": commit.id,
                    "message": commit.message,
                    "url": commit.web_url,
                    "committed_date": _gitlab_datetime_to_odoo(commit.committed_date),
                }
            )
        self.env["gitlab.commit"].create(create_values)
        if not commits:
            return
        self.with_delay(max_retries=0)._import_commits(page + 1, per_page, since, until)

    def import_issues(self):
        until = fields.Datetime.now()

        for project in self:
            since = datetime.min
            last_issue = self.env["gitlab.issue"].search(
                [("project_id", "=", project.id)], order="updated_at desc", limit=1
            )
            if last_issue:
                since = last_issue.updated_at
                # Adding a second to avoid duplicate issues on the boundary
                since += relativedelta(seconds=1)

            project.with_delay(max_retries=0)._import_issues(
                1, project.gitlab_id.per_page, since, until
            )

    def _import_issues(self, page, per_page, since, until):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        project = conn.projects.get(self.external_id)
        params = {
            "page": page,
            "per_page": per_page,
            "updated_before": fields.Datetime.to_string(until),
            "order_by": "updated_at",
            "scope": "all",
            "sort": "asc",
            "state": "all",
        }
        if since > datetime.min:
            params.update(updated_after=fields.Datetime.to_string(since))
        issues = project.issues.list(**params)
        create_values = []
        updated_issues = self.env["gitlab.issue"]
        for issue in issues:
            issue_iid = str(issue.iid)
            existing_issue = self.issue_ids.filtered(
                lambda i: i.external_id == issue_iid
            )
            if existing_issue:
                existing_issue.write(
                    {
                        "state": issue.state,
                        "updated_at": _gitlab_datetime_to_odoo(issue.updated_at),
                    }
                )
                updated_issues += existing_issue
            else:
                create_values.append(
                    {
                        "project_id": self.id,
                        "external_id": issue_iid,
                        "name": issue.title,
                        "description": issue.description,
                        "author_username": issue.author["username"],
                        "url": issue.web_url,
                        "created_at": _gitlab_datetime_to_odoo(issue.created_at),
                        "state": issue.state,
                        "updated_at": _gitlab_datetime_to_odoo(issue.updated_at),
                        "closed_at": _gitlab_datetime_to_odoo(issue.closed_at),
                    }
                )
        new_issues = self.env["gitlab.issue"].create(create_values)
        (updated_issues + new_issues).import_notes()

        if not issues:
            return
        self.with_delay(max_retries=0)._import_issues(page + 1, per_page, since, until)

    def import_merge_requests(self):
        until = fields.Datetime.now()

        for project in self:
            since = datetime.min
            last_mr = self.env["gitlab.merge.request"].search(
                [("project_id", "=", project.id)], order="updated_at desc", limit=1
            )
            if last_mr:
                since = last_mr.updated_at
                # Adding a second to avoid duplicate MRs on the boundary
                since += relativedelta(seconds=1)

            project.with_delay(max_retries=0)._import_merge_requests(
                1, project.gitlab_id.per_page, since, until
            )

    def _import_merge_requests(self, page, per_page, since, until):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        project = conn.projects.get(self.external_id)
        params = {
            "page": page,
            "per_page": per_page,
            "updated_before": fields.Datetime.to_string(until),
            "order_by": "updated_at",
            "scope": "all",
            "sort": "asc",
            "state": "all",
        }
        if since > datetime.min:
            params.update(updated_after=fields.Datetime.to_string(since))
        mrs = project.mergerequests.list(**params)
        create_values = []
        updated_merge_requests = self.env["gitlab.merge.request"]
        for mr in mrs:
            mr_iid = str(mr.iid)
            existing_mr = self.merge_request_ids.filtered(
                lambda m: m.external_id == mr_iid
            )
            if existing_mr:
                existing_mr.write(
                    {
                        "state": mr.state,
                        "updated_at": _gitlab_datetime_to_odoo(mr.updated_at),
                    }
                )
                updated_merge_requests += existing_mr
            else:
                create_values.append(
                    {
                        "project_id": self.id,
                        "external_id": mr_iid,
                        "name": mr.title,
                        "description": mr.description,
                        "author_username": mr.author["username"],
                        "url": mr.web_url,
                        "created_at": _gitlab_datetime_to_odoo(mr.created_at),
                        "state": mr.state,
                        "updated_at": _gitlab_datetime_to_odoo(mr.updated_at),
                        "closed_at": _gitlab_datetime_to_odoo(mr.closed_at),
                        "merged_at": _gitlab_datetime_to_odoo(mr.merged_at),
                    }
                )
        new_merge_requests = self.env["gitlab.merge.request"].create(create_values)
        all_merge_requests = updated_merge_requests + new_merge_requests
        all_merge_requests.import_notes()
        all_merge_requests.import_approvals()

        if not mrs:
            return
        # Sometimes Gitlab returns 99 items, yet there are more pages
        self.with_delay(max_retries=0)._import_merge_requests(
            page + 1, per_page, since, until
        )
