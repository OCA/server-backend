# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


class TestUserRoleCompany(TransactionCase):
    def setUp(self):
        super().setUp()
        # COMPANIES
        self.Company = self.env["res.company"]
        self.company1 = self.env.ref("base.main_company")
        self.company2 = self.Company.create({"name": "company2"})
        # GROUPS for roles
        self.groupA = self.env.ref("base.group_user")
        self.groupB = self.env.ref("base.group_system")
        self.groupC = self.env.ref("base.group_partner_manager")
        # ROLES
        self.Role = self.env["res.users.role"]
        self.roleA = self.Role.create({"name": "ROLE All Companies"})
        self.roleA.implied_ids |= self.groupA
        self.roleB = self.Role.create({"name": "ROLE Company 1"})
        self.roleB.implied_ids |= self.groupB
        self.roleC = self.Role.create({"name": "ROLE Company 1 and 2"})
        self.roleC.implied_ids |= self.groupC
        # USER
        # ==Role=== ==Company== C1  C2  C1+C2
        # Role A                Yes Yes Yes
        # Role B    Company1    Yes
        # Role C    Company1    Yes     Yes
        # Role C    Company2        Yes Yes
        self.User = self.env["res.users"]
        user_vals = {
            "name": "ROLES TEST USER",
            "login": "test_user",
            "company_ids": [(6, 0, [self.company1.id, self.company2.id])],
            "role_line_ids": [
                (0, 0, {"role_id": self.roleA.id}),
                (0, 0, {"role_id": self.roleB.id, "company_id": self.company1.id}),
                (0, 0, {"role_id": self.roleC.id, "company_id": self.company1.id}),
                (0, 0, {"role_id": self.roleC.id, "company_id": self.company2.id}),
            ],
        }
        self.test_user = self.User.create(user_vals)

    def test_110_company_1(self):
        "Company 1 selected: Roles A, B and C are enabled"
        self.test_user.with_context(
            active_company_ids=self.company1.ids
        ).set_groups_from_roles()
        expected = self.groupA | self.groupB | self.groupC
        found = self.test_user.groups_id.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)

    def test_120_company_2(self):
        "Company 2 selected: Roles A and C are enabled"
        self.test_user.with_context(
            active_company_ids=self.company2.ids
        ).set_groups_from_roles()
        enabled = self.test_user.groups_id
        expected = self.groupA | self.groupC
        found = enabled.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)

        not_expected = self.groupB
        found = enabled.filtered(lambda x: x in not_expected)
        self.assertFalse(found)

    def test_130_all_company(self):
        "All Company selected: Roles A and C are enabled"
        self.test_user.with_context(
            active_company_ids=[self.company1.id, self.company2.id]
        ).set_groups_from_roles()
        enabled = self.test_user.groups_id
        expected = self.groupA | self.groupC
        found = enabled.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)

        not_expected = self.groupB
        found = enabled.filtered(lambda x: x in not_expected)
        self.assertFalse(found)
