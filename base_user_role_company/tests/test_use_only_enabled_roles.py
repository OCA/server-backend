# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestUserRoleCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company1 = cls.env.ref("base.main_company")
        # GROUPS for roles
        cls.groupA = cls.env.ref("base.group_user")
        cls.groupB = cls.env.ref("base.group_system")
        # ROLES
        cls.Role = cls.env["res.users.role"]
        cls.roleA = cls.Role.create({"name": "Role internal user"})
        cls.roleA.implied_ids |= cls.groupA
        cls.roleB = cls.Role.create({"name": "Role system user"})
        # USER with roles
        cls.roleB.implied_ids |= cls.groupB
        cls.User = cls.env["res.users"]
        user_vals = {
            "name": "Role test user",
            "login": "role_test_user",
            "company_ids": [(fields.Command.set([cls.company1.id]))],
            "role_line_ids": [
                (fields.Command.create({"role_id": cls.roleA.id})),
                (
                    fields.Command.create(
                        {
                            "role_id": cls.roleB.id,
                            "date_to": fields.Date.today() + timedelta(days=1),
                        }
                    )
                ),
            ],
        }
        cls.test_user = cls.User.create(user_vals)

    def test_110_enabled_role_is_used(self):
        # User should be in group A and B because date_to is in the future
        self.test_user.with_context(
            active_company_ids=self.company1.ids
        ).set_groups_from_roles()
        expected = self.groupA | self.groupB
        found = self.test_user.groups_id.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)

    def test_120_disabled_role_is_not_used(self):
        # User should not be in group B because date_to is in the past
        self.test_user.role_line_ids.filtered(
            lambda x: x.role_id == self.roleB
        ).date_to = fields.Date.today() - timedelta(days=1)
        self.test_user.with_context(
            active_company_ids=self.company1.ids
        ).set_groups_from_roles()
        expected = self.groupA
        found = self.test_user.groups_id.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)
