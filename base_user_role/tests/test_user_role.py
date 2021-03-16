# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import fields
from odoo.tests.common import SavepointCase


class TestUserRole(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_model = cls.env['res.users']
        cls.role_model = cls.env['res.users.role']

        cls.user_admin = cls.env.ref('base.user_admin')
        cls.default_user = cls.env.ref('base.default_user')
        cls.user_id = cls.user_model.create(
            {'name': "USER TEST (ROLES)", 'login': 'user_test_roles'})

        # ROLE_1
        cls.group_user_id = cls.env.ref('base.group_user')
        cls.group_no_one_id = cls.env.ref('base.group_no_one')
        vals = {
            'name': "ROLE_1",
            'implied_ids': [
                (6, 0, [cls.group_user_id.id, cls.group_no_one_id.id])],
        }
        cls.role1_id = cls.role_model.create(vals)

        # ROLE_2
        # Must have group_user in order to have sufficient groups. Check:
        # github.com/odoo/odoo/commit/c3717f3018ce0571aa41f70da4262cc946d883b4
        cls.group_multi_currency_id = cls.env.ref(
            'base.group_multi_currency')
        cls.group_settings_id = cls.env.ref('base.group_system')
        vals = {
            'name': "ROLE_2",
            'implied_ids': [
                (6, 0, [cls.group_user_id.id,
                        cls.group_multi_currency_id.id,
                        cls.group_settings_id.id])],
        }
        cls.role2_id = cls.role_model.create(vals)
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create({"name": "company2"})
        cls.user_id.write(
            {
                "company_ids": [
                    (4, cls.company1.id, 0),
                    (4, cls.company2.id, 0),
                ]
            }
        )

    def test_role_1(self):
        self.user_id.write(
            {"role_line_ids": [(0, 0, {"role_id": self.role1_id.id})]}
        )
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        role_group_ids = self.role1_id.trans_implied_ids.ids
        role_group_ids.append(self.role1_id.group_id.id)
        role_group_ids = sorted(set(role_group_ids))
        self.assertEqual(user_group_ids, role_group_ids)

    def test_role_2(self):
        self.user_id.write(
            {"role_line_ids": [(0, 0, {"role_id": self.role2_id.id})]}
        )
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
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
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
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
                    (
                        0,
                        0,
                        {"role_id": self.role1_id.id, "date_from": today_str},
                    ),
                    # Role 2 should be disabled
                    (
                        0,
                        0,
                        {
                            "role_id": self.role2_id.id,
                            "date_to": yesterday_str,
                        },
                    ),
                ]
            }
        )
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        role1_group_ids = self.role1_id.trans_implied_ids.ids
        role1_group_ids.append(self.role1_id.group_id.id)
        role_group_ids = sorted(set(role1_group_ids))
        self.assertEqual(user_group_ids, role_group_ids)

    def test_role_unlink(self):
        # Get role1 and role2 groups
        role1_groups = self.role1_id.implied_ids | self.role1_id.group_id
        role2_groups = self.role2_id.implied_ids | self.role2_id.group_id
        # Configure the user with role1 and role2
        self.user_id.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role1_id.id}),
                    (0, 0, {"role_id": self.role2_id.id}),
                ]
            }
        )
        # Check user has groups from role1 and role2
        self.assertLessEqual(role1_groups, self.user_id.groups_id)
        self.assertLessEqual(role2_groups, self.user_id.groups_id)
        # Remove role2
        self.role2_id.unlink()
        # Check user has groups from only role1
        self.assertLessEqual(role1_groups, self.user_id.groups_id)
        self.assertFalse(role2_groups <= self.user_id.groups_id)
        # Remove role1
        self.role1_id.unlink()
        # Check user has no groups from role1 and role2
        self.assertFalse(role1_groups <= self.user_id.groups_id)
        self.assertFalse(role2_groups <= self.user_id.groups_id)

    def test_role_line_unlink(self):
        # Get role1 and role2 groups
        role1_groups = self.role1_id.implied_ids | self.role1_id.group_id
        role2_groups = self.role2_id.implied_ids | self.role2_id.group_id
        # Configure the user with role1 and role2
        self.user_id.write(
            {
                "role_line_ids": [
                    (0, 0, {"role_id": self.role1_id.id}),
                    (0, 0, {"role_id": self.role2_id.id}),
                ]
            }
        )
        # Check user has groups from role1 and role2
        self.assertLessEqual(role1_groups, self.user_id.groups_id)
        self.assertLessEqual(role2_groups, self.user_id.groups_id)
        # Remove role2 from the user
        self.user_id.role_line_ids.filtered(
            lambda l: l.role_id.id == self.role2_id.id
        ).unlink()
        # Check user has groups from only role1
        self.assertLessEqual(role1_groups, self.user_id.groups_id)
        self.assertFalse(role2_groups <= self.user_id.groups_id)
        # Remove role1 from the user
        self.user_id.role_line_ids.filtered(
            lambda l: l.role_id.id == self.role1_id.id
        ).unlink()
        # Check user has no groups from role1 and role2
        self.assertFalse(role1_groups <= self.user_id.groups_id)
        self.assertFalse(role2_groups <= self.user_id.groups_id)

    def test_default_user_roles(self):
        self.default_user.write({
            'role_line_ids': [
                (0, 0, {
                    'role_id': self.role1_id.id,
                }),
                (0, 0, {
                    'role_id': self.role2_id.id,
                })
            ]
        })
        # Using normal user instead of superuser, to make sure access
        # rights are not preventing from creating user.
        user = self.user_model.sudo(self.user_admin).create({
            'name': "USER TEST (DEFAULT ROLES)",
            'login': 'user_test_default_roles'
        })
        roles = self.role_model.browse([self.role1_id.id, self.role2_id.id])
        self.assertEqual(user.role_ids, roles)

    def test_default_user_roles_multicompany(self):
        """Get default roles when template user is from other company."""
        company_2 = self.env['res.company'].create({'name': 'New Company'})
        company_2_id = company_2.id
        self.user_admin.write({
            'company_ids': [(4, company_2_id)],
            'company_id': company_2_id
        })
        self.default_user.write({
            'role_line_ids': [
                (0, 0, {
                    'role_id': self.role1_id.id,
                }),
                (0, 0, {
                    'role_id': self.role2_id.id,
                })
            ]
        })
        user = self.user_model.sudo(self.user_admin).create({
            'name': "USER TEST (DEFAULT ROLES)",
            'login': 'user_test_default_roles'
        })
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
                        {
                            "role_id": self.role2_id.id,
                            "company_id": self.company2.id,
                        },
                    )
                ]
            }
        )
        # Check that user does not have any groups
        self.assertEquals(
            self.user_id.groups_id, self.env["res.groups"].browse()
        )

    def test_user_role_same_company(self):
        self.user_id.write({"company_id": self.company1.id})
        self.user_id.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {
                            "role_id": self.role1_id.id,
                            "company_id": self.company1.id,
                        },
                    )
                ]
            }
        )
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
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
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        role_group_ids = self.role2_id.trans_implied_ids.ids
        role_group_ids.append(self.role2_id.group_id.id)
        role_group_ids = sorted(set(role_group_ids))
        # Check that user have groups implied by role 2
        self.assertEqual(user_group_ids, role_group_ids)

    def test_user_role_category(self):
        # Check that groups created by role has the correct
        # default category
        self.assertEqual(
            self.env.ref("base_user_role.ir_module_category_role").id,
            self.role1_id.category_id.id
        )
