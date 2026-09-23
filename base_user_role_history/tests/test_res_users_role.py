from datetime import date

from odoo.addons.base.tests.common import BaseCommon


class TestResUsersRole(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResUsers = cls.env["res.users"]
        cls.ResUsersRole = cls.env["res.users.role"]
        cls.ResUsersRoleLine = cls.env["res.users.role.line"]
        cls.BaseUserRoleLineHistory = cls.env["base.user.role.line.history"]

        cls.user = cls.ResUsers.create(
            {
                "name": "Test user 01",
                "login": "test1",
            }
        )

    def test_create_adds_history(self):
        # act
        role_01 = self.ResUsersRole.create(
            {"name": "Test role 01", "line_ids": [(0, 0, {"user_id": self.user.id})]}
        )

        # assert
        self.assertTrue(role_01.name, "Test role 01")

        history_lines_all = self.BaseUserRoleLineHistory.search(
            [("user_id", "=", self.user.id)]
        )
        self.assertEqual(len(history_lines_all), 1)

        history_line_1 = history_lines_all[0]
        self.assertEqual(history_line_1.user_id, self.user)
        self.assertEqual(history_line_1.performed_action, "add")
        self.assertFalse(history_line_1.old_role_id)
        self.assertEqual(history_line_1.new_role_id, role_01)
        self.assertFalse(history_line_1.old_is_enabled)
        self.assertTrue(history_line_1.new_is_enabled)

    def test_write_adds_history_entry(self):
        # arrange
        role_01 = self.ResUsersRole.create(
            {"name": "Test role 01", "line_ids": [(0, 0, {"user_id": self.user.id})]}
        )

        role_01_line = role_01.line_ids[0]

        # act
        role_01_line.write(
            {
                "date_from": "2024-05-01",
                "date_to": "2024-05-30",
            }
        )

        # assert
        history_lines_all = self.BaseUserRoleLineHistory.search(
            [("user_id", "=", self.user.id)]
        )

        self.assertEqual(len(history_lines_all), 2)

        history_lines_add = history_lines_all.filtered(
            lambda x: x.performed_action == "edit"
        )
        self.assertEqual(len(history_lines_add), 1)

        history_line_1 = history_lines_add[0]
        self.assertEqual(history_line_1.performed_action, "edit")
        self.assertFalse(history_line_1.old_date_from)
        self.assertEqual(history_line_1.new_date_from, date(2024, 5, 1))
        self.assertFalse(history_line_1.old_date_to)
        self.assertEqual(history_line_1.new_date_to, date(2024, 5, 30))
        self.assertTrue(history_line_1.old_is_enabled)
        self.assertTrue(history_line_1.new_is_enabled)

    def test_write_no_history_entry(self):
        # arrange
        role_01 = self.ResUsersRole.create(
            {
                "name": "Test role 01",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "user_id": self.user.id,
                            "date_from": date(2024, 5, 1),
                            "date_to": date(2024, 5, 30),
                        },
                    )
                ],
            }
        )

        role_01_line = role_01.line_ids[0]

        # act
        # write same values again
        role_01_line.write(
            {
                "date_from": date(2024, 5, 1),
                "date_to": date(2024, 5, 30),
            }
        )

        # assert
        history_lines_all = self.BaseUserRoleLineHistory.search(
            [("user_id", "=", self.user.id)]
        )

        self.assertTrue(len(history_lines_all), 1)
        history_lines_edit = history_lines_all.filtered(
            lambda x: x.performed_action == "edit"
        )
        self.assertEqual(len(history_lines_edit), 0)

    def test_create_adds_history_entry(self):
        # arrange
        role_01 = self.ResUsersRole.create({"name": "Test role 01", "line_ids": []})

        # act
        self.ResUsersRoleLine.create(
            {
                "role_id": role_01.id,
                "user_id": self.user.id,
                "date_from": "2024-05-01",
                "date_to": "2024-05-30",
            }
        )

        # assert
        history_line_add = self.BaseUserRoleLineHistory.search(
            [("user_id", "=", self.user.id), ("performed_action", "=", "add")]
        )

        self.assertEqual(len(history_line_add), 1)
        history_line_1 = history_line_add[0]
        self.assertFalse(history_line_1.old_role_id)
        self.assertEqual(history_line_1.new_role_id, role_01)
        self.assertFalse(history_line_1.old_date_from)
        self.assertEqual(history_line_1.new_date_from, date(2024, 5, 1))
        self.assertFalse(history_line_1.old_date_to)
        self.assertEqual(history_line_1.new_date_to, date(2024, 5, 30))
        self.assertFalse(history_line_1.old_is_enabled)
        self.assertTrue(history_line_1.new_is_enabled)

    def test_unlink_adds_history_entry(self):
        # arrange
        role_01 = self.ResUsersRole.create(
            {"name": "Test role 01", "line_ids": [(0, 0, {"user_id": self.user.id})]}
        )

        # act
        role_01.line_ids[0].unlink()

        # assert
        history_line_all = self.BaseUserRoleLineHistory.search(
            [("user_id", "=", self.user.id)]
        )

        self.assertEqual(len(history_line_all), 2)

        history_lines_unlink = history_line_all.filtered(
            lambda x: x.performed_action == "unlink"
        )
        self.assertEqual(len(history_lines_unlink), 1)

        history_line_1 = history_lines_unlink[0]
        self.assertEqual(history_line_1.old_role_id, role_01)
        self.assertFalse(history_line_1.new_role_id)
        self.assertFalse(history_line_1.old_date_from)
        self.assertFalse(history_line_1.new_date_from)
        self.assertFalse(history_line_1.old_date_to)
        self.assertFalse(history_line_1.new_date_to)
        self.assertTrue(history_line_1.old_is_enabled)
        self.assertFalse(history_line_1.new_is_enabled)
