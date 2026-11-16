# Copyright 2026 - GRAP - Sylvain LE GAL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from os import path

from odoo.tests.common import TransactionCase

PATH = path.join(path.dirname(__file__), "import_data", "%s.csv")
FIELDS = ["name", "country_id", "vat"]
OPTIONS = {"headers": True, "quoting": "'", "separator": ","}


class ImportCase(TransactionCase):
    def _import_file(self, disabled=False):
        _file = open(PATH % "res_partner_test")
        record = (
            self.env["base_import.import"]
            .with_context(base_import_strip_disabled=disabled)
            .create(
                {
                    "res_model": "res.partner",
                    "file": _file.read(),
                    "file_name": "%res_partner_test.csv",
                    "file_type": "csv",
                }
            )
        )
        record.execute_import(FIELDS, [], OPTIONS)

    def test_disabled(self):
        self._import_file(disabled=True)
        last_partner = self.env["res.partner"].search([], order="id desc", limit=1)
        self.assertNotEqual(last_partner.name, "Partner Name")

    def test_enabled(self):
        self._import_file(disabled=False)
        last_partner = self.env["res.partner"].search([], order="id desc", limit=1)
        self.assertEqual(last_partner.name, "Partner Name")
        self.assertEqual(last_partner.country_id, self.env.ref("base.fr"))
