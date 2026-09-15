from odoo import Command

from odoo.addons.base.tests.common import TransactionCaseWithUserDemo


class TestResUsers(TransactionCaseWithUserDemo):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_group_backend = cls.env.ref("base_group_backend.base_group_backend")
        cls.internal_user = cls.user_demo
        cls.portal_user = cls.env.ref(
            "base_group_backend.user_demo_external", raise_if_not_found=False
        )
        if not cls.portal_user:
            cls.portal_user = cls._create_user(
                name="Demo partner backend 1",
                login="demo backend user 1",
                groups=[cls.env.ref("base.group_portal").id],
            )
        cls.portal_ui_user = cls.env.ref(
            "base_group_backend.user_demo_external_with_ui", raise_if_not_found=False
        )
        if not cls.portal_ui_user:
            cls.portal_ui_user = cls._create_user(
                name="Demo partner backend 2",
                login="demo backend user 2",
                groups=[cls.env.ref("base_group_backend.group_backend_ui_users").id],
            )
        cls.menu_no_group = cls.env.ref(
            "base_group_backend.menu_root_no_group", raise_if_not_found=False
        )
        if not cls.menu_no_group:
            action = cls.env["ir.actions.act_window"].create(
                {
                    "name": "No Group",
                    "res_model": "res.partner",
                    "view_mode": "list,form",
                }
            )
            cls.menu_no_group = cls.env["ir.ui.menu"].create(
                {"name": "No Group", "sequence": 100}
            )
            cls.env["ir.ui.menu"].create(
                {
                    "name": "No Group Child",
                    "sequence": 100,
                    "parent_id": cls.menu_no_group.id,
                    "action": f"ir.actions.act_window,{action.id}",
                }
            )

    @classmethod
    def _create_user(cls, name, login, groups=None):
        """Helper method to create a user with the specified login and groups."""
        partner = cls.env["res.partner"].create({"name": name})
        user = cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "group_ids": [(6, 0, groups or [])],
                "partner_id": partner.id,
            }
        )
        return user

    def test_has_groups(self):
        self.assertTrue(self.internal_user.has_group("base.group_user"))
        self.assertFalse(self.portal_user.has_group("base.group_user"))
        self.assertTrue(self.portal_ui_user.has_group("base.group_user"))
        self.portal_user.write(
            {"group_ids": [Command.set([self.base_group_backend.id])]}
        )
        self.assertTrue(self.portal_user.has_group("base.group_user"))

    def test_share(self):
        self.assertTrue(self.portal_user.share)
        self.portal_user.write(
            {"group_ids": [Command.set([self.base_group_backend.id])]}
        )
        self.assertFalse(self.portal_user.share)
        self.assertFalse(self.portal_ui_user.share)

    def test_no_roots_menu_with_no_groups(self):
        self.assertNotIn(
            self.menu_no_group,
            self.env["ir.ui.menu"].with_user(self.portal_ui_user).get_user_roots(),
        )
        self.assertIn(
            self.menu_no_group,
            self.env["ir.ui.menu"].with_user(self.internal_user).get_user_roots(),
        )
