import logging
from datetime import datetime
from os.path import dirname, join

import requests
from vcr import VCR

from odoo import fields
from odoo.tests import TransactionCase

logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "vcr_cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization", "PRIVATE-TOKEN"],
    decode_compressed_response=True,
)
_super_send = requests.Session.send


class TestGitlabImport(TransactionCase):
    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return _super_send(s, r, **kw)

    def test_normal_import(self):
        gitlab_id = self.ref("gitlab.gitlab_demo")

        group = self.env["gitlab.group"].create(
            {
                "gitlab_id": gitlab_id,
                "name": "ubports/development/core/flatpak",
                "external_id": 10965795,
            }
        )

        project = self.env["gitlab.project"].create(
            {
                "gitlab_id": gitlab_id,
                "group_id": group.id,
                "name": "ubports/development/core/flatpak/ubuntu-touch-flatpak-runtime",
                "external_id": 10965795,
            }
        )
        until = fields.Datetime.now()
        since = datetime.min
        with recorder.use_cassette("success_imports"):
            group._import_subgroups()
            project._import_issues(1, project.gitlab_id.per_page, since, until)
            project._import_commits(1, project.gitlab_id.per_page, since, until)
            project._import_merge_requests(1, project.gitlab_id.per_page, since, until)
