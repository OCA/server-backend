# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.action_server = cls.env.ref("server_action_sort.sort_action_server_lines")
        cls.line_1 = cls.env.ref("server_action_sort.sort_action_server_lines_line_1")
        cls.line_2 = cls.env.ref("server_action_sort.sort_action_server_lines_line_2")

    def test_action_result(self):
        self.assertEqual(self.line_1.sequence, 1)
        self.assertEqual(self.line_2.sequence, 2)

        # Reorder lines
        self.action_server.with_context(
            active_model="ir.actions.server", active_ids=[self.action_server.id]
        ).run()

        self.assertEqual(self.line_1.sequence, 2)
        self.assertEqual(self.line_2.sequence, 1)
