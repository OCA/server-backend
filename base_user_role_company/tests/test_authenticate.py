# Copyright 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestAuthenticate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company1 = cls.env.ref("base.main_company")
        cls.groupA = cls.env.ref("base.group_user")
        cls.Role = cls.env["res.users.role"]
        cls.roleA = cls.Role.create({"name": "Role authenticate test"})
        cls.roleA.implied_ids |= cls.groupA
        cls.user_with_roles = cls.env["res.users"].create(
            {
                "name": "Auth Test User With Roles",
                "login": "auth_test_with_roles",
                "password": "auth_test_pass_1",
                "company_ids": [Command.set([cls.company1.id])],
                "role_line_ids": [Command.create({"role_id": cls.roleA.id})],
            }
        )
        cls.user_no_roles = cls.env["res.users"].create(
            {
                "name": "Auth Test User No Roles",
                "login": "auth_test_no_roles",
                "password": "auth_test_pass_2",
                "company_ids": [Command.set([cls.company1.id])],
            }
        )

    def test_authenticate_with_roles_applies_groups(self):
        "authenticate() calls set_groups_from_roles() when user has roles"
        # setUpClass already applied groups via create(); strip groupA directly
        # via SQL to bypass ResUsers.write() which calls set_groups_from_roles()
        # and would immediately re-add it.
        self.env.cr.execute(
            "DELETE FROM res_groups_users_rel WHERE uid = %s AND gid = %s",
            (self.user_with_roles.id, self.groupA.id),
        )
        self.user_with_roles.invalidate_recordset(["group_ids"])
        self.assertNotIn(self.groupA, self.user_with_roles.group_ids)
        credential = {
            "login": "auth_test_with_roles",
            "password": "auth_test_pass_1",
            "type": "password",
        }
        auth_info = self.env["res.users"].authenticate(credential, {})
        self.assertIsInstance(auth_info, dict)
        self.assertEqual(auth_info.get("uid"), self.user_with_roles.id)
        self.user_with_roles.invalidate_recordset(["group_ids"])
        self.assertIn(self.groupA, self.user_with_roles.group_ids)

    def test_authenticate_without_roles_no_crash(self):
        "authenticate() returns auth_info without crashing for user without roles"
        credential = {
            "login": "auth_test_no_roles",
            "password": "auth_test_pass_2",
            "type": "password",
        }
        auth_info = self.env["res.users"].authenticate(credential, {})
        self.assertIsInstance(auth_info, dict)
        self.assertEqual(auth_info.get("uid"), self.user_no_roles.id)
