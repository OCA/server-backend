# Copyright 2024 Onestein
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import _
from odoo.tests.common import TransactionCase

from gitlab.client import Gitlab


class TestGitlab(TransactionCase):
    def setUp(self):
        super().setUp()
        self.gitlab = self.env["gitlab"].create({"private_token": "test"})

    def test_name_get(self):
        self.assertTrue(self.gitlab.name_get())

    def test_gitlab_connection(self):
        action = self.gitlab.validate()
        self.assertEqual(action["params"]["title"], _("Connection Test Failed!"))

        def auth(self):
            return True

        with patch.object(
            Gitlab,
            "auth",
            auth,
        ):
            action = self.gitlab.validate()
            self.assertEqual(action["params"]["title"], _("Connection Test Succeeded!"))
