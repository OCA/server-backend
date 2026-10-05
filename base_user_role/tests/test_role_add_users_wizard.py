from odoo import Command
from odoo.tests.common import TransactionCase


class TestRoleAddUsersWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role = cls.env["res.users.role"].create(
            {
                "name": "Test Role",
            }
        )
        cls.user1 = cls.env["res.users"].create(
            {
                "name": "Test User 1",
                "login": "testuser1",
                "email": "testuser1@example.com",
            }
        )
        cls.user2 = cls.env["res.users"].create(
            {
                "name": "Test User 2",
                "login": "testuser2",
                "email": "testuser2@example.com",
            }
        )
        cls.user3 = cls.env["res.users"].create(
            {
                "name": "Test User 3",
                "login": "testuser3",
                "email": "testuser3@example.com",
            }
        )

    def test_add_new_users_to_role(self):
        """Test adding new users to a role without existing users"""
        wizard = self.env["role.add.users.wizard"].create(
            {
                "role_id": self.role.id,
                "user_ids": [Command.set([self.user1.id, self.user2.id])],
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            }
        )

        result = wizard.action_add_users()
        self.assertEqual(result["type"], "ir.actions.act_window_close")
        self.assertEqual(len(self.role.line_ids), 2)
        self.assertIn(self.user1, self.role.line_ids.mapped("user_id"))
        self.assertIn(self.user2, self.role.line_ids.mapped("user_id"))
        for line in self.role.line_ids:
            self.assertEqual(str(line.date_from), "2024-01-01")
            self.assertEqual(str(line.date_to), "2024-12-31")

    def test_add_users_with_existing_users(self):
        """Test adding users when some already exist in the role"""
        self.env["res.users.role.line"].create(
            {
                "role_id": self.role.id,
                "user_id": self.user1.id,
            }
        )

        wizard = self.env["role.add.users.wizard"].create(
            {
                "role_id": self.role.id,
                "user_ids": [Command.set([self.user1.id, self.user2.id])],
            }
        )

        wizard.action_add_users()
        self.assertEqual(len(self.role.line_ids), 2)
        users_in_role = self.role.line_ids.mapped("user_id")
        self.assertIn(self.user1, users_in_role)
        self.assertIn(self.user2, users_in_role)

        user1_lines = self.role.line_ids.filtered(
            lambda line: line.user_id == self.user1
        )
        self.assertEqual(len(user1_lines), 1)

    def test_add_users_without_dates(self):
        """Test adding users without specifying dates"""
        wizard = self.env["role.add.users.wizard"].create(
            {
                "role_id": self.role.id,
                "user_ids": [Command.set([self.user3.id])],
            }
        )

        wizard.action_add_users()
        self.assertEqual(len(self.role.line_ids), 1)
        line = self.role.line_ids[0]
        self.assertEqual(line.user_id, self.user3)
        self.assertFalse(line.date_from)
        self.assertFalse(line.date_to)

    def test_add_multiple_new_users(self):
        """Test adding multiple new users at once"""
        wizard = self.env["role.add.users.wizard"].create(
            {
                "role_id": self.role.id,
                "user_ids": [
                    Command.set([self.user1.id, self.user2.id, self.user3.id])
                ],
                "date_from": "2024-06-01",
            }
        )

        wizard.action_add_users()
        self.assertEqual(len(self.role.line_ids), 3)
        users_in_role = self.role.line_ids.mapped("user_id")
        self.assertEqual(
            set(users_in_role.ids), {self.user1.id, self.user2.id, self.user3.id}
        )
        for line in self.role.line_ids:
            self.assertEqual(str(line.date_from), "2024-06-01")
