# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields

from odoo.addons.base_user_group_mgmt.tests.common import TestBaseUserGroupMgmtCommon


class TestBaseUserGroupMgmtRole(TestBaseUserGroupMgmtCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Role = cls.env["res.users.role"]
        cls.RoleLine = cls.env["res.users.role.line"]

        cls.role_1 = cls.Role.create(
            {
                "name": "Role 1",
            }
        )

    def _get_user_role(self, user, role):
        return self.RoleLine.search(
            [
                ("user_id", "=", user.id),
                ("role_id", "=", role.id),
            ]
        )

    def test_user_add_role(self):
        request = self.request
        user = self.user_1
        role = self.role_1
        self.assertFalse(bool(self._get_user_role(user, role)))
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "user_add_role",
                "role_ids": [Command.set(role.ids)],
                "user_ids": [Command.set(user.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertTrue(bool(self._get_user_role(user, role)))

    def test_user_role_edit(self):
        request = self.request
        user = self.user_1
        role = self.role_1

        role_line = self.RoleLine.create(
            {
                "user_id": user.id,
                "role_id": role.id,
            }
        )

        new_date = fields.Date.today()
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "user_role_edit",
                "role_ids": [Command.set(role.ids)],
                "user_ids": [Command.set(user.ids)],
                "role_date_from": new_date,
                "role_date_to": new_date,
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertEqual(role_line.date_from, new_date)
        self.assertEqual(role_line.date_to, new_date)

    def test_user_remove_role(self):
        request = self.request
        user = self.user_1
        role = self.role_1

        self.RoleLine.create(
            {
                "user_id": user.id,
                "role_id": role.id,
            }
        )

        self.assertTrue(bool(self._get_user_role(user, role)))
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "user_remove_role",
                "role_ids": [Command.set(role.ids)],
                "user_ids": [Command.set(user.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertFalse(bool(self._get_user_role(user, role)))

    def test_role_add_group(self):
        request = self.request
        group_1 = self.group_1
        role = self.role_1
        self.assertNotIn(group_1, role.implied_ids)

        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "role_add_group",
                "group_1_ids": [Command.set(group_1.ids)],
                "role_ids": [Command.set(role.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertIn(group_1, role.implied_ids)
        self.assertEqual(line.state, "done")

    def test_role_remove_group(self):
        request = self.request
        group_1 = self.group_1
        role = self.role_1
        role.write(
            {
                "implied_ids": [Command.link(group_1.id)],
            }
        )

        self.assertIn(group_1, role.implied_ids)

        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "role_remove_group",
                "group_1_ids": [Command.set(group_1.ids)],
                "role_ids": [Command.set(role.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertNotIn(group_1, role.implied_ids)
