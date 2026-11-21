# Copyright 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from uuid import uuid4

from odoo import Command
from odoo.tests.common import HOST, HttpCase


class TestSessionInfo(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create(
            {"name": "Session Test Company 2"}
        )
        cls.groupA = cls.env.ref("base.group_user")
        cls.groupB = cls.env.ref("base.group_system")
        cls.Role = cls.env["res.users.role"]
        cls.roleA = cls.Role.create({"name": "Role session all companies"})
        cls.roleA.implied_ids |= cls.groupA
        cls.roleB = cls.Role.create({"name": "Role session company1 only"})
        cls.roleB.implied_ids |= cls.groupB
        cls.session_user_password = "session_test_pass"
        cls.session_user = cls.env["res.users"].create(
            {
                "name": "Session Test User",
                "login": "session_test_user",
                "password": cls.session_user_password,
                "company_ids": [
                    Command.set([cls.company1.id, cls.company2.id])
                ],
                "role_line_ids": [
                    Command.create({"role_id": cls.roleA.id}),
                    Command.create(
                        {"role_id": cls.roleB.id, "company_id": cls.company1.id}
                    ),
                ],
            }
        )

    def _call_session_info(self, cids=None):
        payload = json.dumps(
            {"jsonrpc": "2.0", "method": "call", "id": str(uuid4())}
        )
        if cids is not None:
            self.opener.cookies.set(
                "cids", "-".join(str(c) for c in cids), domain=HOST
            )
        else:
            self.opener.cookies.pop("cids", None)
        return self.url_open(
            "/web/session/get_session_info",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

    def _get_user_groups(self):
        self.session_user.invalidate_recordset(["group_ids"])
        return self.session_user.group_ids

    def test_session_info_single_company(self):
        "session_info() with single company cids: both roleA and roleB apply"
        self.authenticate(
            self.session_user.login, self.session_user_password
        )
        response = self._call_session_info(cids=[self.company1.id])
        self.assertEqual(response.status_code, 200)
        groups = self._get_user_groups()
        self.assertIn(self.groupA, groups)
        self.assertIn(self.groupB, groups)

    def test_session_info_multi_company_cids(self):
        "session_info() with multi-company cids: roleB excluded (only covers company1)"
        self.authenticate(
            self.session_user.login, self.session_user_password
        )
        response = self._call_session_info(
            cids=[self.company1.id, self.company2.id]
        )
        self.assertEqual(response.status_code, 200)
        groups = self._get_user_groups()
        self.assertIn(self.groupA, groups)
        self.assertNotIn(self.groupB, groups)

    def test_session_info_no_cids_cookie(self):
        "session_info() without cids cookie falls back to user main company"
        self.authenticate(
            self.session_user.login, self.session_user_password
        )
        # Establish known state: remove groupB by selecting both companies
        self._call_session_info(cids=[self.company1.id, self.company2.id])
        self.assertNotIn(self.groupB, self._get_user_groups())
        # Verify the no-cids fallback (main company = company1) restores groupB
        response = self._call_session_info()
        self.assertEqual(response.status_code, 200)
        groups = self._get_user_groups()
        self.assertIn(self.groupA, groups)
        self.assertIn(self.groupB, groups)
