from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    def setUp(self):
        super(TestResUsers, self).setUp()
        self.group_backend = self.env.ref("group_backend.group_backend")
        self.internal_user = self.env.ref("base.user_demo")
        self.portal_user = self.env.ref("base.demo_user0")

    def test_has_groups(self):
        self.assertFalse(self.portal_user.has_group("base.group_user"))
        self.assertTrue(self.internal_user.has_group("base.group_user"))
        self.portal_user.write({"groups_id": [(6, 0, [self.group_backend.id])]})
        self.assertTrue(self.portal_user.has_group("base.group_user"))
