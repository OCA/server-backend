# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval

from odoo.addons.server_action_navigate import hooks


class TestModule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.action_server = self.env.ref(
            "server_action_navigate.navigate_partner_2_tags"
        )
        self.navigate_line_1 = self.env.ref("server_action_navigate.navigate_line_1")
        self.navigate_line_2 = self.env.ref("server_action_navigate.navigate_line_2")
        self.users = self.env["res.users"].search([])

    def test_action_result(self):
        result = self.action_server.with_context(
            active_model="res.users", active_ids=self.users.ids
        ).run()

        self.assertEqual(result.get("id", False), False)

        self.assertEqual(result.get("res_model", False), "res.partner.category")

        self.assertEqual(
            safe_eval(result.get("domain", [])),
            [("id", "in", self.users.mapped("partner_id.category_id").ids)],
        )

    def test_compute_field_domain(self):
        self.assertEqual(self.navigate_line_1.field_domain_model_id.model, "res.users")
        self.assertEqual(
            self.navigate_line_2.field_domain_model_id.model, "res.partner"
        )

    def test_delete_last_line(self):
        line_qty = len(self.action_server.navigate_line_ids)
        self.action_server.delete_last_line()
        self.assertEqual(line_qty - 1, len(self.action_server.navigate_line_ids))

    def test_action_navigate_with_action(self):
        self.action_server.navigate_action_id = self.env.ref(
            "base.action_partner_category_form"
        )

        result = self.action_server.with_context(
            active_model="res.users", active_ids=self.users.ids
        ).run()

        self.assertEqual(
            result.get("id", False),
            self.env.ref("base.action_partner_category_form").id,
        )

    def test_module_uninstall(self):
        self.assertTrue(self.action_server.exists())
        hooks.uninstall_hook(self.env.cr, self.env.registry)
        self.assertFalse(self.action_server.exists())
