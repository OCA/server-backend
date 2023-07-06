# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo.tests.common import TransactionCase


class EffectivePermissionsCase(TransactionCase):
    def test_effective_permissions(self):
        """Test effective permissions of base.user_demo"""
        action = self.env.ref("base.user_demo").action_show_effective_permissions()
        permissions = self.env["res.users.effective.permission"].search(
            action["domain"]
        )
        self.assertTrue(
            permissions.filtered(
                lambda x: x.model_name == "res.company"
            ).read_permission
        )
