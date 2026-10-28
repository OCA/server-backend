# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from unittest.mock import patch

from odoo import Command, http
from odoo.tests import common


class TestSessionInfo(common.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_password = "password"
        cls.user = common.new_test_user(
            cls.env, "user_test_profile", password=cls.user_password
        )
        cls.profile = cls.env["res.users.profile"].create({"name": "profile"})
        cls.role = cls.env["res.users.role"].create(
            {
                "name": "ROLE_1",
                "implied_ids": [Command.set([cls.env.ref("base.group_user").id])],
                "profile_id": cls.profile.id,
            }
        )
        cls.user.write({"role_line_ids": [Command.create({"role_id": cls.role.id})]})

    def test_session_info_authenticate(self):
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": common.get_db_name(),
                    "login": self.user.login,
                    "password": self.user_password,
                },
            }
        )
        with patch.object(http, "db_list", return_value=["db1", "db2"]):
            response = self.url_open(
                "/web/session/authenticate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
        result = response.json()["result"]
        self.assertEqual(result["profile_id"], self.profile.id)
