from odoo import api, fields, models


class Commit(models.Model):
    _name = "gitlab.commit"
    _description = "Gitlab Commit"
    _rec_name = "external_id"

    project_id = fields.Many2one(
        comodel_name="gitlab.project", string="Project", required=True
    )
    external_id = fields.Char(string="External ID", required=True)
    message = fields.Text()
    author_name = fields.Char()
    author_email = fields.Char()
    committed_date = fields.Datetime(required=True)
    url = fields.Char(string="URL", required=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Author Partner",
        compute="_compute_partner_id",
        store=True,
    )

    @api.depends("author_email")
    def _compute_partner_id(self):
        for commit in self:
            partner_id = self.env["res.partner"].get_by_gitlab_email(
                commit.author_email
            )
            commit.partner_id = partner_id

    def reconcile_partner(self):
        self._compute_partner_id()

    _sql_constraints = [
        (
            "unique_commit_per_project",
            "unique(project_id, external_id)",
            "The commit must be unique per project.",
        ),
    ]
