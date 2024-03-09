from odoo import Command
from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_group_backend = cls.env.ref("base_group_backend.base_group_backend")
        cls.internal_user = cls.env.ref("base.user_demo")
        cls.portal_user = cls.env.ref("base_group_backend.user_demo_external")
        cls.portal_ui_user = cls.env.ref(
            "base_group_backend.user_demo_external_with_ui"
        )

    def test_has_groups(self):
        self.assertTrue(self.internal_user.has_group("base.group_user"))
        self.assertFalse(self.portal_user.has_group("base.group_user"))
        self.assertTrue(self.portal_ui_user.has_group("base.group_user"))
        self.portal_user.write(
            {"groups_id": [Command.set([self.base_group_backend.id])]}
        )
        self.assertTrue(self.portal_user.has_group("base.group_user"))

    def test_share(self):
        self.assertTrue(self.portal_user.share)
        self.portal_user.write(
            {"groups_id": [Command.set([self.base_group_backend.id])]}
        )
        self.assertFalse(self.portal_user.share)
        self.assertFalse(self.portal_ui_user.share)
