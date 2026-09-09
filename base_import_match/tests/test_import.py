# Copyright 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# Copyright 2016 Tecnativa - Vicent Cubells
# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

OPTIONS = {
    "headers": True,
    "quoting": '"',
    "separator": ",",
}


class ImportCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]

    def _base_import_record(self, res_model, data):
        """Create and return a ``base_import.import`` record for ``data``."""
        return self.env["base_import.import"].create(
            {
                "res_model": res_model,
                "file": data,
                "file_name": "test.csv",
                "file_type": "csv",
            }
        )

    def _create_rule(self, model, fields_spec, sequence=10):
        """Create a ``base_import.match`` rule.

        :param str model: technical model name, e.g. ``res.partner``.
        :param list fields_spec: list of ``(field_name, imported_value)`` tuples.
            A non-``None`` ``imported_value`` makes the field conditional.
        :param int sequence: rule sequence (lower is evaluated first).
        """
        model_slug = model.replace(".", "_")
        field_lines = []
        for field_name, imported_value in fields_spec:
            vals = {
                "field_id": self.env.ref(f"base.field_{model_slug}__{field_name}").id
            }
            if imported_value is not None:
                vals.update(conditional=True, imported_value=imported_value)
            field_lines.append((0, 0, vals))
        return self.env["base_import.match"].create(
            {
                "model_id": self.env.ref(f"base.model_{model_slug}").id,
                "sequence": sequence,
                "field_ids": field_lines,
            }
        )

    def test_res_partner_external_id(self):
        """An external ID keeps updating the record when rules apply."""
        self._create_rule("res.partner", [("name", None)])
        partner = self.Partner.create({"name": "External ID Original"})
        xmlid = partner.export_data(["id"])["datas"][0][0]
        record = self._base_import_record(
            "res.partner", f"{xmlid},External ID Changed\n"
        )
        record.execute_import(["id", "name"], [], OPTIONS)
        partner.env.cache.invalidate()
        self.assertEqual(partner.name, "External ID Changed")

    def test_res_partner_dbid(self):
        """A database ID keeps updating the record when rules apply."""
        self._create_rule("res.partner", [("name", None)])
        partner_1 = self.Partner.create({"name": "DBID One"})
        partner_2 = self.Partner.create({"name": "DBID Two"})
        # The match logic resolves a dbid to its external id, so ensure both exist.
        partner_1.export_data(["id"])
        partner_2.export_data(["id"])
        record = self._base_import_record(
            "res.partner",
            f"{partner_1.id},DBID One Changed\n{partner_2.id},DBID Two Changed\n",
        )
        record.execute_import([".id", "name"], [], OPTIONS)
        partner_1.env.cache.invalidate()
        self.assertEqual(partner_1.name, "DBID One Changed")
        self.assertEqual(partner_2.name, "DBID Two Changed")

    def test_res_partner_vat(self):
        """Match a company by VAT (shipped rule) and update its name."""
        partner = self.Partner.create(
            {"name": "VAT Original", "vat": "BE0477472701", "is_company": True}
        )
        record = self._base_import_record(
            "res.partner", "VAT Changed,BE0477472701,True\n"
        )
        record.execute_import(["name", "vat", "is_company"], [], OPTIONS)
        partner.env.cache.invalidate()
        self.assertEqual(partner.name, "VAT Changed")

    def test_res_partner_invalid_combination_vat(self):
        """A failed rule condition does not update the record."""
        partner = self.Partner.create(
            {"name": "Invalid Original", "vat": "BE0477472701", "is_company": True}
        )
        original_name = partner.name
        record = self._base_import_record(
            "res.partner", "Invalid Changed,BE0477472701,False\n"
        )
        record.execute_import(["name", "vat", "is_company"], [], OPTIONS)
        partner.env.cache.invalidate()
        self.assertEqual(partner.name, original_name)

    def test_res_partner_email(self):
        """Match a partner by email and update its name."""
        self._create_rule("res.partner", [("email", None)])
        partner = self.Partner.create(
            {"name": "Email Original", "email": "match@example.com"}
        )
        record = self._base_import_record(
            "res.partner", "match@example.com,Email Changed\n"
        )
        record.execute_import(["email", "name"], [], OPTIONS)
        partner.env.cache.invalidate()
        self.assertEqual(partner.name, "Email Changed")

    def test_res_partner_name(self):
        """Match a partner by name and update its job position."""
        self._create_rule("res.partner", [("name", None)])
        partner = self.Partner.create({"name": "Name Match"})
        record = self._base_import_record(
            "res.partner", "Function Changed,Name Match\n"
        )
        record.execute_import(["function", "name"], [], OPTIONS)
        partner.env.cache.invalidate()
        self.assertEqual(partner.function, "Function Changed")

    def test_res_partner_name_duplicated(self):
        """With duplicate names, a more specific rule (email) disambiguates."""
        self._create_rule("res.partner", [("email", None)], sequence=10)
        self._create_rule("res.partner", [("name", None)], sequence=20)
        partner_1 = self.Partner.create(
            {"name": "Duplicated Name", "email": "first@example.com"}
        )
        partner_2 = self.Partner.create(
            {"name": "Duplicated Name", "email": "second@example.com"}
        )
        original_function = partner_1.function
        record = self._base_import_record(
            "res.partner", "Function Changed,Duplicated Name,second@example.com\n"
        )
        record.execute_import(["function", "name", "email"], [], OPTIONS)
        partner_1.env.cache.invalidate()
        self.assertEqual(partner_1.function, original_function)
        self.assertEqual(partner_2.function, "Function Changed")

    def test_res_partner_parent_name_is_company(self):
        """Match a child contact by parent, name and is_company; update email."""
        self._create_rule(
            "res.partner",
            [("name", None), ("parent_id", None), ("is_company", None)],
        )
        parent = self.Partner.create({"name": "Parent Company", "is_company": True})
        parent_xmlid = parent.export_data(["id"])["datas"][0][0]
        child = self.Partner.create(
            {"name": "Child Contact", "is_company": False, "parent_id": parent.id}
        )
        record = self._base_import_record(
            "res.partner",
            f"Child Contact,False,{parent_xmlid},child.changed@example.com\n",
        )
        record.execute_import(
            ["name", "is_company", "parent_id/id", "email"], [], OPTIONS
        )
        child.env.cache.invalidate()
        self.assertEqual(child.email, "child.changed@example.com")

    def test_match_only_from_ui(self):
        """Match by email via UI selection, update function, don't write email."""
        partner = self.Partner.create(
            {"name": "Match Partner", "email": "match@example.com"}
        )
        record = self._base_import_record(
            "res.partner", data="match@example.com,New Function\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        record.execute_import(["email", "function"], [], options)
        partner.env.cache.invalidate()
        self.assertEqual(partner.function, "New Function")
        self.assertEqual(partner.email, "match@example.com")

    def test_match_only_name_reporting(self):
        """A match-only column before ``name`` must not corrupt result['name'].

        Core reports imported record names by indexing the original columns it
        passed to ``load()``; dropping the match-only column in place would shift
        that index and surface the match value (email) instead of the name.
        """
        partner = self.Partner.create(
            {"name": "Report Original", "email": "report@example.com"}
        )
        record = self._base_import_record(
            "res.partner", data="report@example.com,Report Changed\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        result = record.execute_import(["email", "name"], [], options)
        partner.env.cache.invalidate()
        # The DB write targets the right column...
        self.assertEqual(partner.name, "Report Changed")
        # ...and the reported name is the name column, not the match-only email.
        self.assertEqual(result["name"][0], "Report Changed")
        self.assertNotIn("report@example.com", result["name"])

    def test_match_only_no_match_blocks(self):
        """When match-only field doesn't find a record, block the import."""
        record = self._base_import_record(
            "res.partner", data="nonexistent@example.com,New Partner\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        count_before = self.Partner.search_count([])
        result = record.execute_import(["email", "name"], [], options)
        count_after = self.Partner.search_count([])
        self.assertEqual(count_after, count_before)
        self.assertFalse(result["ids"])
        self.assertTrue(result["messages"])
        self.assertIn("No matching record found", result["messages"][0]["message"])

    def test_match_only_multiple_match_blocks(self):
        """When match-only field finds multiple records, block the import."""
        self.Partner.create({"name": "Dup 1", "email": "dup@example.com"})
        self.Partner.create({"name": "Dup 2", "email": "dup@example.com"})
        record = self._base_import_record(
            "res.partner", data="dup@example.com,Updated Name\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        result = record.execute_import(["email", "name"], [], options)
        self.assertFalse(result["ids"])
        self.assertTrue(result["messages"])
        self.assertIn(
            "Multiple matching records found", result["messages"][0]["message"]
        )

    def test_match_only_empty_value_used_as_criteria(self):
        """Empty imported value is still used as a match criterion."""
        self.Partner.create(
            {"name": "Test", "email": "test@example.com", "vat": "BE123"}
        )
        record = self._base_import_record(
            "res.partner", data="test@example.com,,New Function\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email", "vat"])
        result = record.execute_import(["email", "vat", "function"], [], options)
        # email matches but vat doesn't (empty vs "BE123"), so import is blocked
        self.assertFalse(result["ids"])
        self.assertTrue(result["messages"])

    def test_match_only_partial_match_blocks_all(self):
        """One row matches, one doesn't: entire import blocked."""
        partner = self.Partner.create(
            {"name": "Existing", "email": "exists@example.com"}
        )
        original_name = partner.name
        record = self._base_import_record(
            "res.partner",
            data="exists@example.com,Updated\nnope@example.com,New\n",
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        count_before = self.Partner.search_count([])
        result = record.execute_import(["email", "name"], [], options)
        count_after = self.Partner.search_count([])
        # Entire import blocked — no new record, existing not updated
        self.assertFalse(result["ids"])
        self.assertTrue(result["messages"])
        self.assertEqual(count_after, count_before)
        self.assertEqual(partner.name, original_name)

    def test_match_only_empty_skips_rules(self):
        """Empty match-only list from UI skips matching even if rules exist."""
        partner = self.Partner.create(
            {"name": "VAT Partner", "vat": "BE0411905847", "is_company": True}
        )
        original_name = partner.name
        record = self._base_import_record(
            "res.partner", data="Changed Name,BE0411905847,True\n"
        )
        # Empty list = user unchecked everything in UI -> no matching
        options = dict(OPTIONS, import_match_only_fields=[])
        count_before = self.Partner.search_count([])
        record.execute_import(["name", "vat", "is_company"], [], options)
        count_after = self.Partner.search_count([])
        partner.env.cache.invalidate()
        # Should create a new record, not update the existing one
        self.assertEqual(count_after, count_before + 1)
        self.assertEqual(partner.name, original_name)

    def test_res_users_login(self):
        """Match a user by login (shipped rule) and update its name."""
        user = self.env["res.users"].create(
            {"login": "match_login_user", "name": "Login Original"}
        )
        record = self._base_import_record(
            "res.users", "match_login_user,Login Changed\n"
        )
        record.execute_import(["login", "name"], [], OPTIONS)
        user.env.cache.invalidate()
        self.assertEqual(user.name, "Login Changed")
