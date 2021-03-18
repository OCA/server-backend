from odoo import Command
from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_group_backend = cls.env.ref("base_group_backend.group_backend")
        cls.internal_user = cls.env.ref("base.user_demo")
        cls.portal_user = cls.env.ref("base.demo_user0")

    def test_has_groups(self):
        self.assertFalse(self.portal_user.has_group("base.group_user"))
        self.assertTrue(self.internal_user.has_group("base.group_user"))
        self.portal_user.write(
            {"groups_id": [Command.set([self.base_group_backend.id])]}
        )
        self.assertTrue(self.portal_user.has_group("base.group_user"))
