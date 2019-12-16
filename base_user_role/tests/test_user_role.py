# Copyright 2014 ABF OSIELL <http://osiell.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import datetime

from odoo import fields
from odoo.tests.common import TransactionCase


class TestUserRole(TransactionCase):
    def setUp(self):
        super(TestUserRole, self).setUp()
        self.user_model = self.env["res.users"]
        self.role_model = self.env["res.users.role"]

        self.default_user = self.env.ref("base.default_user")
        self.user_id = self.user_model.create(
            {"name": "USER TEST (ROLES)", "login": "user_test_roles"}
        )

        # ROLE_1
        self.group_user_id = self.env.ref("base.group_user")
        self.group_no_one_id = self.env.ref("base.group_no_one")
        vals = {
            "name": "ROLE_1",
            "implied_ids": [(6, 0, [self.group_user_id.id, self.group_no_one_id.id])],
        }
        self.role1_id = self.role_model.create(vals)

        # ROLE_2
        # Must have group_user in order to have sufficient groups. Check:
        # github.com/odoo/odoo/commit/c3717f3018ce0571aa41f70da4262cc946d883b4
        self.group_multi_currency_id = self.env.ref("base.group_multi_currency")
        self.group_settings_id = self.env.ref("base.group_system")
        vals = {
            "name": "ROLE_2",
            "implied_ids": [
                (
                    6,
                    0,
                    [
                        self.group_user_id.id,
                        self.group_multi_currency_id.id,
                        self.group_settings_id.id,
                    ],
                )
            ],
        }
        self.role2_id = self.role_model.create(vals)
        self.company1 = self.env.ref("base.main_company")
        self.company2 = self.env["res.company"].create({"name": "company2"})
        self.user_id.write(
            {"company_ids": [(4, self.company1.id, 0), (4, self.company2.id, 0)]}
        )

    def test_role_1(self):
        self.user_id.write({"role_line_ids": [(0, 0, {"role_id": self.role1_id.id})]})
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        role_group_ids = self.role1_id.trans_implied_ids.ids
        role_group_ids.append(self.role1_id.group_id.id)
        role_group_ids = sorted(set(role_group_ids))
        self.assertEqual(user_group_ids, role_group_ids)

    def test_role_2(self):
        self.user_id.write({"role_line_ids": [(0, 0, {"role_id": self.role2_id.id})]})
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        role_group_ids = self.role2_id.trans_implied_ids.ids
        role_group_ids.append(self.role2_id.group_id.id)
        role_group_ids = sorted(set(role_group_ids))
        self.assertEqual(user_group_ids, role_group_ids)

    def test_role_1_2(self):
        self.user_id.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role1_id.id}),
                    (0, 0, {"role_id": self.role2_id.id}),
                ]
            }
        )
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        role1_group_ids = self.role1_id.trans_implied_ids.ids
        role1_group_ids.append(self.role1_id.group_id.id)
        role2_group_ids = self.role2_id.trans_implied_ids.ids
        role2_group_ids.append(self.role2_id.group_id.id)
        role_group_ids = sorted(set(role1_group_ids + role2_group_ids))
        self.assertEqual(user_group_ids, role_group_ids)

    def test_role_1_2_with_dates(self):
        today_str = fields.Date.today()
        today = fields.Date.from_string(today_str)
        yesterday = today - datetime.timedelta(days=1)
        yesterday_str = fields.Date.to_string(yesterday)
        self.user_id.write(
            {
                "role_line_ids": [
                    # Role 1 should be enabled
                    (0, 0, {"role_id": self.role1_id.id, "date_from": today_str}),
                    # Role 2 should be disabled
                    (0, 0, {"role_id": self.role2_id.id, "date_to": yesterday_str}),
                ]
            }
        )
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        role1_group_ids = self.role1_id.trans_implied_ids.ids
        role1_group_ids.append(self.role1_id.group_id.id)
        role_group_ids = sorted(set(role1_group_ids))
        self.assertEqual(user_group_ids, role_group_ids)

    def test_role_unlink(self):
        # Get role1 groups
        role1_group_ids = self.role1_id.implied_ids.ids
        role1_group_ids.append(self.role1_id.group_id.id)
        role1_group_ids = sorted(set(role1_group_ids))

        # Configure the user with role1 and role2
        self.user_id.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role1_id.id}),
                    (0, 0, {"role_id": self.role2_id.id}),
                ]
            }
        )
        # Remove role2
        self.role2_id.unlink()
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        self.assertEqual(user_group_ids, role1_group_ids)
        # Remove role1
        self.role1_id.unlink()
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        self.assertEqual(user_group_ids, [])

    def test_role_line_unlink(self):
        # Get role1 groups
        role1_group_ids = self.role1_id.implied_ids.ids
        role1_group_ids.append(self.role1_id.group_id.id)
        role1_group_ids = sorted(set(role1_group_ids))

        # Configure the user with role1 and role2
        self.user_id.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role1_id.id}),
                    (0, 0, {"role_id": self.role2_id.id}),
                ]
            }
        )
        # Remove role2 from the user
        self.user_id.role_line_ids.filtered(
            lambda l: l.role_id.id == self.role2_id.id
        ).unlink()
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        self.assertEqual(user_group_ids, role1_group_ids)
        # Remove role1 from the user
        self.user_id.role_line_ids.filtered(
            lambda l: l.role_id.id == self.role1_id.id
        ).unlink()
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        self.assertEqual(user_group_ids, [])

    def test_default_user_roles(self):
        self.default_user.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role1_id.id}),
                    (0, 0, {"role_id": self.role2_id.id}),
                ]
            }
        )
        user = self.user_model.create(
            {"name": "USER TEST (DEFAULT ROLES)", "login": "user_test_default_roles"}
        )
        roles = self.role_model.browse([self.role1_id.id, self.role2_id.id])
        self.assertEqual(user.role_ids, roles)

    def test_user_role_different_company(self):
        self.user_id.write({"company_id": self.company1.id})
        self.user_id.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {"role_id": self.role2_id.id, "company_id": self.company2.id},
                    )
                ]
            }
        )
        # Check that user does not have any groups
        self.assertEquals(self.user_id.groups_id, self.env["res.groups"].browse())

    def test_user_role_same_company(self):
        self.user_id.write({"company_id": self.company1.id})
        self.user_id.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {"role_id": self.role1_id.id, "company_id": self.company1.id},
                    )
                ]
            }
        )
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        role_group_ids = self.role1_id.trans_implied_ids.ids
        role_group_ids.append(self.role1_id.group_id.id)
        role_group_ids = sorted(set(role_group_ids))
        # Check that user have groups implied by role 1
        self.assertEqual(user_group_ids, role_group_ids)

    def test_user_role_no_company(self):
        self.user_id.write({"company_id": self.company1.id})
        self.user_id.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role2_id.id, "company_id": False})
                ]
            }
        )
        user_group_ids = sorted({group.id for group in self.user_id.groups_id})
        role_group_ids = self.role2_id.trans_implied_ids.ids
        role_group_ids.append(self.role2_id.group_id.id)
        role_group_ids = sorted(set(role_group_ids))
        # Check that user have groups implied by role 2
        self.assertEqual(user_group_ids, role_group_ids)
