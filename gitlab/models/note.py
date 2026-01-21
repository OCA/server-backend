from odoo import api, fields, models


class Note(models.Model):
    _name = "gitlab.note"
    _description = "Gitlab Note"

    project_id = fields.Many2one(
        comodel_name="gitlab.project", string="Project", required=True
    )
    external_id = fields.Char(
        string="External ID", required=True
    )  # Char because Gitlab ids are larger than int4
    name = fields.Char(required=True)
    created_at = fields.Datetime()
    author_username = fields.Char(string="Username")
    merge_request_id = fields.Many2one(
        comodel_name="gitlab.merge.request", string="Merge Request", ondelete="cascade"
    )
    issue_id = fields.Many2one(
        comodel_name="gitlab.issue", string="Issue", ondelete="cascade"
    )
    url = fields.Char(string="URL", required=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Author Partner",
        compute="_compute_partner_id",
        store=True,
    )

    @api.depends("author_username")
    def _compute_partner_id(self):
        for note in self:
            partner_id = self.env["res.partner"].get_by_gitlab_username(
                note.author_username
            )
            note.partner_id = partner_id

    def reconcile_partner(self):
        self._compute_partner_id()
