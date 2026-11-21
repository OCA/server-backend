# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestUserRoleCompany(TransactionCase):
    def setUp(self):
        super().setUp()
        # COMPANIES
        self.Company = self.env["res.company"]
        self.company1 = self.env.ref("base.main_company")
        self.company2 = self.Company.create({"name": "company2"})
        self.company3 = self.Company.create({"name": "company3"})
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
            "company_ids": [Command.set([self.company1.id, self.company2.id])],
            "role_line_ids": [
                Command.create({"role_id": self.roleA.id}),
                Command.create(
                    {"role_id": self.roleB.id, "company_id": self.company1.id}
                ),
                Command.create(
                    {"role_id": self.roleC.id, "company_id": self.company1.id}
                ),
                Command.create(
                    {"role_id": self.roleC.id, "company_id": self.company2.id}
                ),
            ],
        }
        self.test_user = self.User.create(user_vals)

    def test_110_company_1(self):
        "Company 1 selected: Roles A, B and C are enabled"
        self.test_user.with_context(
            active_company_ids=self.company1.ids
        ).set_groups_from_roles()
        expected = self.groupA | self.groupB | self.groupC
        found = self.test_user.group_ids.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)

    def test_120_company_2(self):
        "Company 2 selected: Roles A and C are enabled"
        self.test_user.with_context(
            active_company_ids=self.company2.ids
        ).set_groups_from_roles()
        enabled = self.test_user.group_ids
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
        enabled = self.test_user.group_ids
        expected = self.groupA | self.groupC
        found = enabled.filtered(lambda x: x in expected)
        self.assertEqual(expected, found)

        not_expected = self.groupB
        found = enabled.filtered(lambda x: x in not_expected)
        self.assertFalse(found)

    def test_140_company_3(self):
        "Company 3 selected: ValidationError"
        user_vals = {
            "name": "ROLES TEST USER 2",
            "login": "test_user_2",
            "company_ids": [Command.set([self.company1.id, self.company2.id])],
            "role_line_ids": [
                Command.create(
                    {"role_id": self.roleA.id, "company_id": self.company3.id}
                ),
            ],
        }
        with self.assertRaises(ValidationError):
            self.User.create(user_vals)

    def test_150_no_context_fallback(self):
        "No active_company_ids context: falls back to user main company"
        self.assertEqual(
            self.test_user.company_id,
            self.company1,
            "Guard: test_user main company must be company1 for this test to be valid",
        )
        # roles active for company1: roleA (global), roleB (company1), roleC (company1 line)
        enabled = self.test_user._get_enabled_roles()
        role_ids = enabled.mapped("role_id")
        self.assertIn(self.roleA, role_ids)
        self.assertIn(self.roleB, role_ids)
        self.assertIn(self.roleC, role_ids)
        # roleC line scoped to company2 should NOT be active under company1 alone
        enabled_companies = enabled.filtered(
            lambda l: l.role_id == self.roleC
        ).mapped("company_id")
        self.assertNotIn(self.company2, enabled_companies)

    def test_160_check_role_company_secondary_ok(self):
        "Role assigned to a secondary company (in company_ids) does not raise"
        # company2 is not the main company but IS in test_user.company_ids
        line = self.test_user.role_line_ids.filtered(
            lambda l: l.company_id == self.company2
        )
        self.assertTrue(line, "Expected a role line for company2")
        # _check_role_company should not raise
        line._check_role_company()

    def test_170_role_uniq_same_company_blocked(self):
        "Assigning the same role to the same company twice raises an error"
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["res.users.role.line"].create(
                    {
                        "user_id": self.test_user.id,
                        "role_id": self.roleB.id,
                        "company_id": self.company1.id,
                    }
                )
                self.env.flush_all()

    def test_180_role_uniq_different_company_allowed(self):
        "Assigning the same role to different companies succeeds"
        # roleA is currently assigned without company_id (global)
        # Assigning it again for company1 specifically should succeed
        self.env["res.users.role.line"].create(
            {
                "user_id": self.test_user.id,
                "role_id": self.roleA.id,
                "company_id": self.company1.id,
            }
        )
        lines = self.test_user.role_line_ids.filtered(
            lambda l: l.role_id == self.roleA
        )
        self.assertEqual(len(lines), 2)
