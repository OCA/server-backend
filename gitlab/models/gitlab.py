from odoo import api, fields, models

import gitlab


class Gitlab(models.Model):
    _name = "gitlab"
    _description = "Gitlab Connection"

    url = fields.Char(string="URL", default="https://gitlab.com")
    private_token = fields.Char(string="Private / Personal Token", required=True)
    debug = fields.Boolean(string="Enable Debug Mode")
    per_page = fields.Integer(string="Pagination", default=100)

    @api.depends("url")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.url

    def get_server_connection(self):
        self.ensure_one()
        conn = gitlab.Gitlab(
            url=self.url, private_token=self.private_token, retry_transient_errors=True
        )  # Use the gitlab library rate limiting and retry logic instead of
        # RetryableJobError, because GitlabHttpError doesn't include rate limit headers,
        # if this is blocking other jobs you should create a separate channel
        if self.debug:
            conn.enable_debug()
        return conn

    def validate(self):
        conn = self.get_server_connection()
        conn.auth()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": self.env._("Connection Test Successful"),
                "type": "success",
            },
        }

    @api.model
    def cron_import(self):
        for project in self.env["gitlab.project"].search([]):
            project.import_commits()
            project.import_issues()
            project.import_merge_requests()

    @api.model
    def cron_update_throughtput_times(self):
        issues = self.env["gitlab.issue"].search([("state", "!=", "closed")])
        issues._compute_throughtput_time()
        merge_requests = self.env["gitlab.merge.request"].search(
            [("state", "not in", ("merged", "closed"))]
        )
        merge_requests._compute_throughtput_time()
