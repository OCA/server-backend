# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, Command
from odoo.tests.common import TransactionCase


class TestBaseGrouperUser(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.User = cls.env["res.users"].with_context(no_reset_password=True)
        cls.Group = cls.env["res.groups"]

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

    def test_edit_user(self):
        base_group = self.user_group
        new_user = self.User.with_user(self.user).create(
            {
                "name": "test2",
                "login": "test2",
                "groups_id": [
                    Command.link(base_group.id),
                ],
            }
        )

        new_user_sudo = new_user.with_user(SUPERUSER_ID)
        self.assertFalse(bool(new_user_sudo.groups_id))

        new_user.write(
            {
                "groups_id": [
                    Command.link(base_group.id),
                ]
            }
        )
        new_user_sudo.invalidate_recordset()
        self.assertFalse(bool(new_user_sudo.groups_id))

        new_user_sudo.write(
            {
                "groups_id": [
                    Command.link(base_group.id),
                ]
            }
        )
        self.assertIn(base_group, new_user_sudo.groups_id)

    def test_edit_groups(self):
        base_group = self.user_group
        group = self.Group.with_user(self.user).create(
            {
                "name": "Test group 1",
                "category_id": self.category_hidden.id,
                "implied_ids": [
                    Command.link(base_group.id),
                ],
            }
        )
        group_sudo = group.with_user(SUPERUSER_ID)
        self.assertFalse(bool(group_sudo.implied_ids))

        group.write(
            {
                "implied_ids": [
                    Command.link(base_group.id),
                ]
            }
        )
        group_sudo.invalidate_recordset()
        self.assertFalse(bool(group_sudo.implied_ids))

        group_sudo.write(
            {
                "implied_ids": [
                    Command.link(base_group.id),
                ]
            }
        )
        self.assertEqual(group_sudo.implied_ids, base_group)
