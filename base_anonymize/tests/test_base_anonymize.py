# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.tests.common import Form, TransactionCase


class TestBaseAnonymize(TransactionCase):
    def test_anonymization(self):
        user = self.env.ref("base.user_demo")
        self.assertTrue(user.image_1920)

        org_email = user.email
        org_name = user.name

        self.env["anonymize.wizard"].action_run()

        self.env.clear()

        self.assertNotEqual(user.email, org_email)
        self.assertNotEqual(user.name, org_name)
        self.assertFalse(user.image_1920)

    def test_ui(self):
        field_definition = self.env.ref(
            "base_anonymize.anon_ir_attachment__datas_account_move"
        )
        self.assertTrue(field_definition.applicable)

        with Form(field_definition) as form:
            form.model_id = self.env.ref("base.model_ir_model")
            self.assertEqual(form.model_name, "ir.model")
            form.field_id = self.env.ref("base.field_ir_model__name")
            self.assertEqual(form.field_name, "name")
            form.method = "anonymize.method.fixed.string"

        action = field_definition.action_options()

        self.env[action["res_model"]].with_context(action["context"]).create(
            {
                "string": "hello world",
            }
        )

        self.assertEqual(field_definition.options, '{"string": "hello world"}')
