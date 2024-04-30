# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.tests.common import TransactionCase


class TestUserGroupReadonly(TransactionCase):
    def test_group_update(self):
        """Test that group is updated by cron"""
        cron = self.env.ref('user_group_readonly.cron_update_group_readonly')
        group = self.env.ref('user_group_readonly.group_readonly')
        group.model_access = False
        cron.method_direct_trigger()
        self.assertTrue(group.model_access)
