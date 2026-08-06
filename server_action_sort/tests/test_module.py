# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        model_server_action = cls.env["ir.model"].search(
            [("model", "=", "ir.actions.server")], limit=1
        )
        sort_line_field = cls.env["ir.model.fields"].search(
            [
                ("model_id", "=", model_server_action.id),
                ("name", "=", "sort_line_ids"),
            ],
            limit=1,
        )
        sort_line_model = cls.env["ir.model"].search(
            [("model", "=", "ir.actions.server.sort.line")], limit=1
        )
        field_name_field = cls.env["ir.model.fields"].search(
            [("model_id", "=", sort_line_model.id), ("name", "=", "field_name")],
            limit=1,
        )
        desc_field = cls.env["ir.model.fields"].search(
            [("model_id", "=", sort_line_model.id), ("name", "=", "desc")],
            limit=1,
        )
        cls.action_server = cls.env["ir.actions.server"].create(
            {
                "name": "Test Sort Action",
                "state": "sort",
                "model_id": model_server_action.id,
                "sort_field_id": sort_line_field.id,
            }
        )
        cls.line_1 = cls.env["ir.actions.server.sort.line"].create(
            {
                "sequence": 1,
                "action_id": cls.action_server.id,
                "field_id": field_name_field.id,
                "desc": False,
            }
        )
        cls.line_2 = cls.env["ir.actions.server.sort.line"].create(
            {
                "sequence": 2,
                "action_id": cls.action_server.id,
                "field_id": desc_field.id,
                "desc": False,
            }
        )

    def test_action_result(self):
        self.assertEqual(self.line_1.sequence, 1)
        self.assertEqual(self.line_2.sequence, 2)

        # Reorder lines
        self.action_server.with_context(
            active_model="ir.actions.server", active_ids=[self.action_server.id]
        ).run()

        self.line_1.invalidate_recordset()
        self.line_2.invalidate_recordset()
        self.assertEqual(self.line_1.sequence, 2)
        self.assertEqual(self.line_2.sequence, 1)
