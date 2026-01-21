from odoo import api, fields, models


class Group(models.Model):
    _name = "gitlab.group"
    _description = "Gitlab Group"
    _parent_name = "parent_id"
    _parent_store = True

    gitlab_id = fields.Many2one(comodel_name="gitlab", string="Gitlab", required=True)
    name = fields.Char(required=True)
    external_id = fields.Char(
        string="External ID", store=True, readonly=True, compute="_compute_external_id"
    )
    project_ids = fields.One2many(
        comodel_name="gitlab.project",
        inverse_name="group_id",
        string="Projects",
    )
    parent_path = fields.Char(index=True)
    parent_id = fields.Many2one(string="Parent", comodel_name="gitlab.group")
    child_ids = fields.One2many(
        comodel_name="gitlab.group",
        inverse_name="parent_id",
        string="Subgroups",
    )

    _sql_constraints = [
        (
            "unique_gitlab_group",
            "unique(gitlab_id, name)",
            "The group name must be unique per Gitlab instance.",
        ),
        (
            "unique_external_id",
            "unique(gitlab_id, external_id)",
            "The external ID must be unique per Gitlab instance.",
        ),
    ]

    @api.depends("name", "gitlab_id")
    def _compute_external_id(self):
        for rec in self:
            external_id = False
            if rec.gitlab_id and rec.name:
                conn = rec.gitlab_id.get_server_connection()
                group = conn.groups.get(rec.name)
                external_id = group.id
            rec.external_id = external_id

    def import_subgroups(self):
        self.with_delay()._import_subgroups()

    def _import_subgroups(self):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        group = conn.groups.get(self.name, max_retries=-1)

        existing_groups = self.child_ids
        existing_groups_map = existing_groups.mapped("external_id")
        subgroups = group.subgroups.list(
            get_all=True, all_available=True, max_retries=-1
        )

        for subgroup in subgroups:
            subgroup_id = str(subgroup.id)
            if subgroup_id not in existing_groups_map:
                gitlab_group = self.env["gitlab.group"].create(
                    {
                        "gitlab_id": self.gitlab_id.id,
                        "parent_id": self.id,
                        "name": subgroup.full_path,
                        "external_id": subgroup_id,
                    }
                )
            else:
                gitlab_group = existing_groups.filtered(
                    lambda g: g.external_id == subgroup_id
                )
            gitlab_group.with_delay()._import_subgroups()

    def import_projects(self):
        self.with_delay()._import_projects()

    def _import_projects(self):
        self.ensure_one()
        conn = self.gitlab_id.get_server_connection()
        group = conn.groups.get(self.name, max_retries=-1)
        projects = group.projects.list(get_all=True, max_retries=-1)

        existing_projects = self.project_ids.mapped("external_id")
        create_values = []

        for project in projects:
            project_id = str(project.id)
            if project_id not in existing_projects:
                create_values.append(
                    {
                        "gitlab_id": self.gitlab_id.id,
                        "group_id": self.id,
                        "name": project.name,
                        "external_id": project_id,
                        "url": project.web_url,
                    }
                )
        self.env["gitlab.project"].create(create_values)

        for subgroup in self.child_ids:
            subgroup.with_delay()._import_projects()
