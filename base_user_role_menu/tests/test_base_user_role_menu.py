# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestBaseUserRoleMenu(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_a = cls.env["res.groups"].create({"name": "Test Group A"})
        cls.group_b = cls.env["res.groups"].create({"name": "Test Group B"})

        cls.group_parent = cls.env["res.groups"].create(
            {
                "name": "Test Group Parent",
            }
        )

        cls.role_a = cls.env["res.users.role"].create({"name": "Role A"})
        cls.role_b = cls.env["res.users.role"].create({"name": "Role B"})
        cls.role_parent = cls.env["res.users.role"].create({"name": "Role Parent"})

        cls.role_a.write({"implied_ids": [(4, cls.group_a.id)]})
        cls.role_b.write({"implied_ids": [(4, cls.group_b.id)]})
        cls.role_parent.write({"implied_ids": [(4, cls.role_a.group_id.id)]})

        cls.menu_a = cls.env["ir.ui.menu"].create(
            {
                "name": "Test Menu A",
                "groups_id": [(4, cls.role_a.group_id.id)],
            }
        )
        cls.menu_b = cls.env["ir.ui.menu"].create(
            {
                "name": "Test Menu B",
                "groups_id": [(4, cls.role_b.group_id.id)],
            }
        )
        cls.menu_both = cls.env["ir.ui.menu"].create(
            {
                "name": "Test Menu Both",
                "groups_id": [(4, cls.role_a.group_id.id), (4, cls.role_b.group_id.id)],
            }
        )
        cls.menu_free = cls.env["ir.ui.menu"].create({"name": "Test Menu Free"})

    def test_menu_with_single_group_returns_matching_role(self):
        self.assertIn(self.role_a, self.menu_a.role_ids)
        self.assertNotIn(self.role_b, self.menu_a.role_ids)

    def test_menu_with_two_groups_returns_both_roles(self):
        self.assertIn(self.role_a, self.menu_both.role_ids)
        self.assertIn(self.role_b, self.menu_both.role_ids)

    def test_menu_without_groups_has_no_role(self):
        self.assertTrue(self.menu_free.has_no_role)
        self.assertFalse(self.menu_free.role_ids)

    def test_implied_group_propagates_role(self):
        self.menu_a._compute_role_ids()
        self.assertIn(self.role_parent, self.menu_a.role_ids)
