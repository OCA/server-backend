# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, Command
from odoo.tests.common import TransactionCase


class TestBaseGrouperUserRole(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.User = cls.env["res.users"].with_context(no_reset_password=True)
        cls.Group = cls.env["res.groups"]
        cls.Role = cls.env["res.users.role"]

        cls.user_group = cls.env.ref("base.group_user")
        cls.partner_group = cls.env.ref("base.group_partner_manager")
        cls.erp_user_group = cls.env.ref("base_group_erp_user.group_erp_user")
        cls.category_hidden = cls.env.ref("base.module_category_hidden")

        cls.user = cls.User.create(
            {
                "name": "test",
                "login": "test",
                "groups_id": [
                    Command.link(cls.erp_user_group.id),
                    Command.link(cls.partner_group.id),
                ],
            }
        )

        cls.role = cls.Role.create(
            {
                "name": "Test role",
                "implied_ids": [
                    Command.link(cls.user_group.id),
                ],
            }
        )

    def test_edit_role(self):
        base_group = self.user_group
        role = self.Role.with_user(self.user).create(
            {
                "name": "Test Role 1",
                "implied_ids": [
                    Command.link(base_group.id),
                ],
            }
        )
        role_sudo = role.with_user(SUPERUSER_ID)
        self.assertFalse(bool(role_sudo.implied_ids))

        role.write(
            {
                "implied_ids": [
                    Command.link(base_group.id),
                ]
            }
        )
        role.invalidate_recordset()
        self.assertFalse(bool(role_sudo.implied_ids))

        role_sudo.write(
            {
                "implied_ids": [
                    Command.link(base_group.id),
                ]
            }
        )
        self.assertEqual(role_sudo.implied_ids, base_group)
