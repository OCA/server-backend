# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBaseAnonymize(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.partner"].create(
            {
                "name": "Rossi Meccanica S.r.l.",
                "is_company": True,
                "email": "info@rossi-meccanica.it",
                "street": "Via Roma 1",
                "city": "Latina",
                "zip": "04100",
                "website": "https://rossi-meccanica.it",
            }
        )
        cls.person = cls.env["res.partner"].create(
            {
                "name": "Mario Rossi",
                "parent_id": cls.company.id,
                "email": "mario.rossi@rossi-meccanica.it",
                "phone": "+39 0773 123456",
            }
        )
        # in SQL: base_vat, when installed, would check the number
        cls.env.cr.execute(
            "UPDATE res_partner SET vat='IT00000000000' WHERE id=%s", [cls.company.id]
        )
        cls.env.invalidate_all()
        cls.own_company = cls.env.company.partner_id
        cls.own_company_name = cls.own_company.name
        cls.root_name = cls.env.ref("base.partner_root").name
        cls.env["ir.config_parameter"].sudo().set_param("database.is_neutralized", True)

    def _run(self):
        # the file store garbage collection deletes files outside the
        # transaction: a test must not run it
        with patch.object(
            type(self.env["ir.attachment"]), "_gc_file_store_unsafe"
        ) as gc:
            self.env["anonymize.wizard"].action_run()
        gc.assert_called_once()
        self.env.invalidate_all()

    def test_partners(self):
        self._run()
        company, person = self.company, self.person
        self.assertEqual(company.name, f"Company {company.id}")
        self.assertNotEqual(person.name, "Mario Rossi")
        self.assertTrue(person.name)
        self.assertEqual(person.email, f"partner{person.id}@example.com")
        self.assertEqual(person.phone, f"+39 000 {person.id}")
        self.assertEqual(company.street, f"Street {company.id}")
        self.assertFalse(company.vat)
        self.assertFalse(company.website)
        # kept on purpose: needed for taxes and fiscal positions
        self.assertEqual(company.city, "Latina")
        self.assertEqual(company.zip, "04100")
        # stored copies follow the new values
        self.assertEqual(person.commercial_company_name, company.name)
        self.assertEqual(person.complete_name, f"{company.name}, {person.name}")
        if "email_normalized" in person._fields:
            self.assertEqual(person.email_normalized, person.email)
        # the companies of the database and OdooBot are not anonymized
        self.assertEqual(self.own_company.name, self.own_company_name)
        self.assertEqual(self.env.ref("base.partner_root").name, self.root_name)

    def test_users(self):
        user = self.env.ref("base.user_demo", raise_if_not_found=False)
        if not user:
            user = self.env["res.users"].create(
                {"name": "Demo", "login": "demo@rossi-meccanica.it"}
            )
        admin = self.env.ref("base.user_admin")
        self.public_login = self.env.ref("base.public_user").login
        self._run()
        self.assertEqual(user.login, f"user{user.id}@example.com")
        self.assertEqual(admin.login, "admin")
        self.assertEqual(self.env.ref("base.public_user").login, self.public_login)
        password = (
            self.env["ir.config_parameter"].sudo().get_param("base_anonymize.password")
        )
        self.assertTrue(password)
        self.env.cr.execute("SELECT password FROM res_users WHERE id=%s", [admin.id])
        hashed = self.env.cr.fetchone()[0]
        self.assertTrue(self.env["res.users"]._crypt_context().verify(password, hashed))

    def test_fictional_name_modulo(self):
        """A record whose id is a multiple of the number of names is anonymized
        too: the first version of the join left it untouched."""
        names = self.env["anonymize.method.fictional.character.data"].search_count([])
        self.env.cr.execute("SELECT max(id) FROM res_partner")
        next_multiple = (self.env.cr.fetchone()[0] // names + 1) * names
        self.env.cr.execute(
            "SELECT setval('res_partner_id_seq', %s)", [next_multiple - 1]
        )
        partner = self.env["res.partner"].create({"name": "Giulia Bianchi"})
        self.assertEqual(partner.id % names, 0)
        self._run()
        self.assertNotEqual(partner.name, "Giulia Bianchi")
        self.assertTrue(partner.name)

    def test_not_stored_field_is_skipped(self):
        definition = self.env["anonymize.field"].create(
            {
                "model_name": "res.partner",
                "field_name": "display_name",
                "method": "anonymize.method.fixed.string",
            }
        )
        self.assertTrue(definition.applicable)
        with self.assertLogs(
            "odoo.addons.base_anonymize.models.anonymize_method", level="WARNING"
        ) as logs:
            self.assertEqual(self.env[definition.method]._run(definition), 0)
        self.assertIn("display_name is not stored", logs.output[0])

    def test_options_and_domain_validation(self):
        definition = self.env.ref("base_anonymize.anon_res_partner__street")
        self.assertEqual(definition._get_options(), {"pattern": "Street {id}"})
        with self.assertRaises(ValidationError):
            definition.options = "not json"
        with self.assertRaises(ValidationError):
            definition.domain = "[('no_such_field', '=', 1)]"

    def test_applicable(self):
        definition = self.env["anonymize.field"].create(
            {
                "model_name": "no.such.model",
                "field_name": "name",
                "method": "anonymize.method.set.null",
            }
        )
        self.assertFalse(definition.applicable)
        applicable = self.env["anonymize.field"].search([("applicable", "=", True)])
        self.assertNotIn(definition, applicable)
        self.assertIn(
            self.env.ref("base_anonymize.anon_res_partner__email"), applicable
        )

    def test_analytic_account(self):
        if "account.analytic.account" not in self.env:
            self.skipTest("analytic not installed")
        plan = self.env["account.analytic.plan"].create({"name": "Projects"})
        account = self.env["account.analytic.account"].create(
            {"name": "Rossi Meccanica", "plan_id": plan.id}
        )
        self._run()
        self.assertEqual(account.name, f"Analytic {account.id}")

    def test_partner_function(self):
        self.person.function = "Assistant to Mario Rossi"
        self._run()
        self.assertFalse(self.person.function)

    def test_sale_order_lines(self):
        if "sale.order" not in self.env:
            self.skipTest("sale not installed")
        product = self.env["product.product"].create({"name": "Maintenance"})
        order = self.env["sale.order"].create(
            {
                "partner_id": self.person.id,
                "note": "<p>Deliver to Mario Rossi</p>",
                "order_line": [
                    (0, 0, {"product_id": product.id, "name": "Visit at Mario Rossi"}),
                    (0, 0, {"display_type": "line_note", "name": "Ask Mario Rossi"}),
                ],
            }
        )
        line_definitions = (
            self.env.ref("base_anonymize.anon_sale_order_line__name")
            .with_context(active_test=False)
            .exists()
        )
        self.assertFalse(line_definitions.active)
        self._run()
        self.assertFalse(order.note)
        self.assertEqual(order.order_line[0].name, "Visit at Mario Rossi")
        line_definitions.active = True
        self._run()
        product_line, note_line = order.order_line
        self.assertEqual(product_line.name, "Maintenance")
        self.assertEqual(note_line.name, f"Line {note_line.id}")

    def test_refuses_database_not_neutralized(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "database.is_neutralized", False
        )
        with self.assertRaises(UserError):
            self.env["anonymize.wizard"].action_run()
        self.assertEqual(self.person.name, "Mario Rossi")

    def _definition(self, model_name, field_name, method, **values):
        return self.env["anonymize.field"].create(
            dict(
                values,
                model_name=model_name,
                field_name=field_name,
                method=method,
            )
        )

    def test_random_methods(self):
        email = self._definition(
            "res.partner",
            "email",
            "anonymize.method.random.email",
            domain=f"[('id', '=', {self.person.id})]",
        )
        number = self._definition(
            "res.partner",
            "color",
            "anonymize.method.random.number",
            domain=f"[('id', '=', {self.person.id})]",
            options='{"min_number": 5, "max_number": 5}',
        )
        self.person.color = 1
        self.assertEqual(self.env[email.method]._run(email), 1)
        self.assertEqual(self.env[number.method]._run(number), 1)
        self.env.invalidate_all()
        self.assertTrue(self.person.email.endswith("@example.com"))
        self.assertNotIn("rossi", self.person.email)
        self.assertEqual(self.person.color, 5)

    def test_translated_field(self):
        category = self.env["res.partner.category"].create({"name": "Mario Rossi"})
        definition = self._definition(
            "res.partner.category",
            "name",
            "anonymize.method.fixed.string",
            domain=f"[('id', '=', {category.id})]",
        )
        self.env[definition.method]._run(definition)
        self.env.invalidate_all()
        self.assertEqual(category.name, "-anonymized-")

    def test_methods_without_work(self):
        name = self._definition(
            "res.partner", "name", "anonymize.method.fictional.character"
        )
        with self.assertRaises(NotImplementedError):
            self.env["anonymize.method"]._run(name)
        # a stored field that is not computed is not recomputed
        recompute = self._definition(
            "res.partner", "name", "anonymize.method.recompute"
        )
        self.assertEqual(self.env[recompute.method]._run(recompute), 0)
        # no product on partners
        product_name = self._definition(
            "res.partner", "name", "anonymize.method.product.name"
        )
        self.assertEqual(self.env[product_name.method]._run(product_name), 0)
        # no fictional names to pick from
        self.env["anonymize.method.fictional.character.data"].search([]).unlink()
        self.assertEqual(self.env[name.method]._run(name), 0)
        self.assertEqual(self.person.name, "Mario Rossi")

    def test_product_name(self):
        if "product.packaging" not in self.env:
            self.skipTest("product not installed")
        product = self.env["product.product"].create({"name": "Maintenance"})
        packaging = self.env["product.packaging"].create(
            {"name": "Box for Mario Rossi", "product_id": product.id}
        )
        definition = self._definition(
            "product.packaging",
            "name",
            "anonymize.method.product.name",
            domain=f"[('id', '=', {packaging.id})]",
        )
        self.assertEqual(self.env[definition.method]._run(definition), 1)
        self.env.invalidate_all()
        self.assertEqual(packaging.name, "Maintenance")

    def test_definition_form(self):
        model = self.env["ir.model"]._get("res.partner")
        field = self.env["ir.model.fields"]._get("res.partner", "email")
        definition = self._definition("res.partner", "name", "anonymize.method.pattern")
        definition.write({"model_id": model.id, "field_id": field.id})
        self.assertEqual(definition.model_name, "res.partner")
        self.assertEqual(definition.field_name, "email")
        self.assertEqual(definition.model_id, model)
        self.assertEqual(definition.field_id, field)
        self.assertIn("pattern", definition.default_options)
        self.assertIn(
            ("anonymize.method.pattern", "Pattern with record id"),
            definition._selection_method(),
        )
        definition.options = False
        with self.assertRaises(ValidationError):
            definition.options = "[1, 2]"
        missing = self._definition("no.such.model", "name", "anonymize.method.set.null")
        self.assertFalse(missing.model_id)
        self.assertFalse(missing.field_id)
        not_applicable = self.env["anonymize.field"].search(
            [("applicable", "=", False)]
        )
        self.assertIn(missing, not_applicable)
        self.assertNotIn(definition, not_applicable)
        with self.assertRaises(NotImplementedError):
            self.env["anonymize.field"].search([("applicable", "in", [True])])

    def test_attachments(self):
        attachment = self.env["ir.attachment"]
        document = attachment.create(
            {
                "name": "cv.txt",
                "raw": b"Mario Rossi, Via Roma 1, Latina",
                "res_model": "res.partner",
                "res_id": self.person.id,
            }
        )
        # attachments of binary fields are anonymized too
        image = attachment.create(
            {
                "name": "image_1920",
                "raw": b"a picture of Mario Rossi",
                "res_model": "res.partner",
                "res_field": "image_1920",
                "res_id": self.person.id,
            }
        )
        other = attachment.create(
            {
                "name": "terms.txt",
                "raw": b"General terms and conditions",
                "res_model": "res.company",
                "res_id": self.env.company.id,
            }
        )
        fnames = {document.store_fname, image.store_fname} - {False}
        manual = self._definition(
            "res.partner",
            "function",
            "anonymize.method.set.null",
            domain=f"[('id', '=', {self.person.id})]",
        )
        with (
            patch.object(type(attachment), "_file_delete") as file_delete,
            self.assertLogs(
                "odoo.addons.base_anonymize.models.anonymize_field", level="INFO"
            ) as logs,
        ):
            self._run()
        for record in document | image:
            self.assertFalse(record.raw)
            self.assertFalse(record.store_fname)
            self.assertFalse(record.db_datas)
            self.assertEqual(record.file_size, 0)
            self.assertEqual(record.checksum, attachment._compute_checksum(b""))
        self.assertEqual(other.raw, b"General terms and conditions")
        # other attachments of partners and users in the database too
        self.assertLessEqual(
            fnames, {call.args[0] for call in file_delete.call_args_list}
        )
        output = "\n".join(logs.output)
        self.assertIn("(base_anonymize.anon_ir_attachment__datas, domain [(", output)
        self.assertIn(f"(anonymize.field {manual.id}, domain [('id', '=',", output)
        self.assertIn("Anonymization done", output)
        # emptied attachments are not counted again
        definition = self.env.ref("base_anonymize.anon_ir_attachment__datas")
        self.assertEqual(self.env[definition.method]._run(definition), 0)
