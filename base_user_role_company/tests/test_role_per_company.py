# Copyright 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestUserRoleCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create({"name": "company2"})

        # By convenience, we will use the model 'ir.model.access' in the tests
        # and check the accesses to it, because this model is only readable
        # by 'base.group_erp_manager'
        cls.group_settings = cls.env.ref("base.group_erp_manager")
        cls.Role = cls.env["res.users.role"]
        cls.role_user = cls.Role.create({"name": "Role - user (all companies)"})
        cls.role_user.implied_ids |= cls.env.ref("base.group_user")
        cls.role_settings = cls.Role.create({"name": "Role - admin (company1 only)"})
        cls.role_settings.implied_ids |= cls.group_settings

        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Company scoping test user",
                "login": "company_scoping_test_user",
                "company_id": cls.company1.id,
                "company_ids": (cls.company1 | cls.company2).ids,
                "role_line_ids": [
                    Command.create({"role_id": cls.role_user.id}),
                    Command.create(
                        {
                            "role_id": cls.role_settings.id,
                            "company_ids": cls.company1.ids,
                        }
                    ),
                ],
            }
        )

    def test_ir_model_access_is_company_aware(self):
        # User browsing on company2
        self.assertIn(self.group_settings, self.test_user.group_ids)
        self.assertFalse(
            self.env["ir.model.access"]
            .with_user(self.test_user)
            .with_context(allowed_company_ids=self.company2.ids)
            .check("ir.model.access", "read", raise_exception=False),
            "On company2, the user is only a user, even if 'base.group_erp_manager' "
            "is written in 'user.group_ids'. Indeed, 'all_group_ids' is computed on-"
            "the-fly and is role-company-aware.",
        )

        # User browsing on company1
        self.assertTrue(
            self.env["ir.model.access"]
            .with_user(self.test_user)
            .with_context(allowed_company_ids=self.company1.ids)
            .check("ir.model.access", "read", raise_exception=False),
            "The access is granted to `ir.model.access`, not because "
            "'base.group_erp_manager' is written in 'user.group_ids' but because "
            "'all_group_ids' compute it and has it on-the-fly.",
        )

    def test_ir_rule_is_company_aware(self):
        """In addons/base/models/ir.rule, the `_compute_domain` is already company-aware
        since v19.0:
        - 'allowed_company_ids' listed in @api.ormcache
        - 'all_group_ids' used in code
        ==> Just ensure `ir.rule` are well aware of company-dependant roles
        like 'ir.model.access'"""
        # Test dataset
        Category = self.env["res.partner.category"]
        visible_with_role, _ = Category.create(
            [
                {"name": "Visible with role"},
                {"name": "Other category"},
            ]
        )
        self.env["ir.rule"].create(
            {
                "name": "Only see one category with group_settings",
                "model_id": self.env["ir.model"]._get("res.partner.category").id,
                "groups": [Command.set([self.group_settings.id])],
                "domain_force": f"[('id', '=', {visible_with_role.id})]",
            }
        )

        categories_on_company1 = (
            Category.with_user(self.test_user)
            .with_context(allowed_company_ids=self.company1.ids)
            .search([])
        )
        self.assertEqual(
            categories_on_company1,
            visible_with_role,
            "The ir.rule should restrict visibility to the first category.",
        )

        categories_on_company2 = (
            Category.with_user(self.test_user)
            .with_context(allowed_company_ids=self.company2.ids)
            .search([])
        )
        self.assertEqual(
            categories_on_company2,
            Category.search([]),
            "The role's group is NOT active on company2, so its ir.rule "
            "must not apply there: every category should be visible.",
        )

    def test_check_company_constrain(self):
        """Ensure the companies of a role line are in the range of user's companies"""
        user_vals = {
            "name": "ROLES TEST USER 2",
            "login": "test_user_2",
            "company_ids": self.company1.ids,
            "role_line_ids": [
                Command.create(
                    {
                        "role_id": self.role_settings.id,
                        "company_ids": self.company2.ids,
                    }
                ),
            ],
        }
        with self.assertRaises(ValidationError):
            self.env["res.users"].create(user_vals)
