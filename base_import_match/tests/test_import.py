# Copyright 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from os import path

from odoo.tests.common import TransactionCase

PATH = path.join(path.dirname(__file__), "import_data", "%s.csv")
OPTIONS = {
    "headers": True,
    "quoting": '"',
    "separator": ",",
}


class ImportCase(TransactionCase):
    def _base_import_record(self, res_model, file_name):
        """Create and return a ``base_import.import`` record."""
        with open(PATH % file_name) as demo_file:
            return self.env["base_import.import"].create(
                {
                    "res_model": res_model,
                    "file": demo_file.read(),
                    "file_name": "%s.csv" % file_name,
                    "file_type": "csv",
                }
            )

    def test_res_partner_external_id(self):
        """Change name based on External ID."""
        deco_addict = self.env.ref("base.res_partner_2")
        record = self._base_import_record("res.partner", "res_partner_external_id")
        record.do(["id", "vat", "name"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, "Deco Addict External ID Changed")

    def test_res_partner_dbid(self):
        """Change name based on DB ID."""
        deco_addict = self.env.ref("base.res_partner_2")
        record = self._base_import_record("res.partner", "res_partner_dbid")
        record.do([".id", "vat", "name"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, "Deco Addict External DBID Changed")

    def test_res_partner_vat(self):
        """Change name based on VAT."""
        deco_addict = self.env.ref("base.res_partner_2")
        deco_addict.vat = "BE0477472701"
        record = self._base_import_record("res.partner", "res_partner_vat")
        record.do(["name", "vat", "is_company"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, "Deco Addict Changed")

    def test_res_partner_invalid_combination_vat(self):
        """Change name based on VAT."""
        deco_addict = self.env.ref("base.res_partner_2")
        deco_addict.vat = "BE0477472701"
        record = self._base_import_record(
            "res.partner", "res_partner_invalid_combination_vat"
        )
        record.do(["name", "vat", "is_company"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, deco_addict.name)

    def test_res_partner_parent_name_is_company(self):
        """Change email based on parent_id, name and is_company."""
        record = self._base_import_record(
            "res.partner", "res_partner_parent_name_is_company"
        )
        record.do(["name", "is_company", "parent_id/id", "email"], [], OPTIONS)
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").email,
            "floyd.steward34.changed@example.com",
        )

    def test_res_partner_email(self):
        """Change name based on email."""
        record = self._base_import_record("res.partner", "res_partner_email")
        record.do(["email", "name"], [], OPTIONS)
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").name, "Floyd Steward Changed"
        )

    def test_res_partner_name(self):
        """Change function based on name."""
        record = self._base_import_record("res.partner", "res_partner_name")
        record.do(["function", "name"], [], OPTIONS)
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").function, "Function Changed"
        )

    def test_res_partner_name_duplicated(self):
        """Change function based on name."""
        record = self._base_import_record("res.partner", "res_partner_name")
        partner_1 = self.env.ref("base.res_partner_address_4")
        partner_2 = self.env.ref("base.res_partner_2")
        function = partner_1.function
        partner_2.name = partner_1.name
        record.do(["function", "name"], [], OPTIONS)
        self.assertEqual(self.env.ref("base.res_partner_address_4").function, function)

    def test_res_users_login(self):
        """Change name based on login."""
        record = self._base_import_record("res.users", "res_users_login")
        record.do(["login", "name"], [], OPTIONS)
        self.assertEqual(self.env.ref("base.user_demo").name, "Demo User Changed")

    def test_res_partner_email_one2many(self):
        """Change function based on email and import one2many record."""
        record = self._base_import_record("res.partner", "res_partner_email_one2many")
        record.do(
            [
                "email",
                "function",
                "child_ids/name",
                "child_ids/color",
                "child_ids/email",
            ],
            [],
            OPTIONS,
        )
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").function, "Bug Fixer"
        )
        self.assertTrue(
            self.env.ref("base.res_partner_address_4").child_ids,
        )
        self.assertEqual(
            len(self.env.ref("base.res_partner_address_4").child_ids),
            3,
        )
        self.assertEqual(
            set(self.env.ref("base.res_partner_address_4").mapped("child_ids.name")),
            {"Bart Steward", "Lisa Steward", "Maggie Steward"},
        )
        self.assertEqual(
            set(self.env.ref("base.res_partner_address_4").mapped("child_ids.email")),
            {
                "bart.steward@example.com",
                "lisa.steward@example.com",
                "maggie.steward@example.com",
            },
        )
        self.assertEqual(
            set(self.env.ref("base.res_partner_address_4").mapped("child_ids.color")),
            {666, 777, 555},
        )
