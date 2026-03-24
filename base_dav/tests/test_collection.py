# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest import mock

import odoo.http as http
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged

from ..radicale.collection import Collection


@tagged("post_install", "-at_install")
class TestCalendar(TransactionCase):
    @classmethod
    def setUpClass(cls):
        """Prepare DAV calendar collection, field mappings and test user record."""
        super().setUpClass()

        cls.collection = cls.env["dav.collection"].create(
            {
                "name": "Test Collection",
                "dav_type": "calendar",
                "model_id": cls.env.ref("base.model_res_users").id,
                "domain": "[]",
            }
        )

        cls._create_field_mapping(
            "login",
            "base.field_res_users__login",
            excode="result = record.login",
            imcode="result = item.value",
        )
        cls._create_field_mapping(
            "name",
            "base.field_res_users__name",
        )

        cls.record = cls.env["res.users"].create(
            {
                "login": "tester",
                "name": "Test User",
            }
        )

    @classmethod
    def _create_field_mapping(cls, name, field_xmlid, imcode=None, excode=None):
        """Create field mapping for DAV collection with optional import/export code."""
        return cls.env["dav.collection.field_mapping"].create(
            {
                "collection_id": cls.collection.id,
                "name": name,
                "field_id": cls.env.ref(field_xmlid).id,
                "mapping_type": "code" if (imcode or excode) else "simple",
                "import_code": imcode,
                "export_code": excode,
            }
        )

    def _compare_record(self, vobj, rec=None):
        """Assert that vobject data matches expected Odoo record values."""
        tmp = self.collection.from_vobject(vobj)
        rec = rec or self.record
        self.assertEqual(rec.login, tmp["login"])
        self.assertEqual(rec.name, tmp["name"])

    def test_import_export(self):
        """Verify that exporting and re-importing a record preserves its data."""
        # Exporting and importing should result in the same record
        vobj = self.collection.to_vobject(self.record)
        self._compare_record(vobj)

    def test_get_record(self):
        """Verify record lookup by ID and by custom UUID field."""
        rec = self.collection.get_record([str(self.record.id)])
        self.assertEqual(rec, self.record)

        self.collection.field_uuid = self.env.ref("base.field_res_users__login")
        rec = self.collection.get_record([self.record.login])
        self.assertEqual(rec, self.record)

    def test_collection_wrapper_list_get_upload_delete(self):
        """Verify DAV collection wrapper list, get, upload and delete operations."""
        req = mock.MagicMock()
        req.env = self.env
        http._request_stack.push(req)
        self.addCleanup(http._request_stack.pop)

        login = self.env.user.login
        collection_path = f"{login}/{self.collection.id}"
        collection = Collection(collection_path)

        record_href = str(self.record.id)

        self.assertIn(record_href, list(collection.list()))

        item = collection.get(record_href)
        self.assertTrue(item)
        self._compare_record(item.vobject_item)
        self.assertEqual(item.href, record_href)

        self.assertFalse(collection.get(record_href + "0"))

        exported = self.collection.to_vobject(self.record)
        self.record.login = "different"
        with self.assertRaises(AssertionError):
            self._compare_record(exported)

        uploaded_item, _replaced = collection.upload(record_href, exported)
        self.assertTrue(uploaded_item)
        self._compare_record(uploaded_item.vobject_item)

        collection.delete(record_href)
        self.assertFalse(self.record.exists())

        new_href = record_href + "0"
        created_item, _ = collection.upload(new_href, exported)
        self.assertTrue(created_item)

        vobj = created_item.vobject_item
        uid_value = vobj.contents["vevent"][0].uid.value or ""

        self.assertTrue(uid_value, "Expected UID to be present")
        self.assertTrue(
            uid_value.isdigit(), "Expected UID to be the record id by default"
        )

        created_id = int(uid_value)
        new_record = (
            self.env[self.collection.model_id.model].browse(created_id).exists()
        )
        self.assertTrue(new_record)
        self.assertNotEqual(new_record, self.record)
        self._compare_record(created_item.vobject_item, new_record)

    def test_collection_helpers_and_negative_paths(self):
        self.assertEqual(
            self.collection._split_path("/a//b/c/"),
            ["a", "b", "c"],
        )
        self.assertTrue(
            self.collection._odoo_to_http_datetime(self.record.write_date).endswith(
                "GMT"
            )
        )
        self.assertEqual(
            self.collection._compute_url.__name__,
            "_compute_url",
        )

        self.collection.field_uuid = self.env.ref("base.field_res_users__login")
        self.assertFalse(self.collection.get_record(["bad.ics"]))
        self.assertEqual(
            self.collection.get_record([f"{self.record.login}.ics"]),
            self.record,
        )

        self.collection.dav_type = "files"
        self.assertIsNone(self.collection.to_vobject(self.record))
        self.assertIsNone(self.collection.from_vobject(mock.Mock(name="whatever")))
        self.assertIsNone(self.collection.dav_upload(mock.Mock(), "/x", mock.Mock()))
        self.assertIsNone(self.collection.dav_delete(mock.Mock(), "/x"))

    def test_compute_tag_and_url_and_datetime_helpers(self):
        """Verify compute helpers and datetime conversion helpers."""
        self.collection.dav_type = "calendar"
        self.collection._compute_tag()
        self.assertEqual(self.collection.tag, "VCALENDAR")

        self.collection.dav_type = "addressbook"
        self.collection._compute_tag()
        self.assertEqual(self.collection.tag, "VADDRESSBOOK")

        self.collection.dav_type = "files"
        self.collection._compute_tag()
        self.assertFalse(self.collection.tag)

        self.env["ir.config_parameter"].sudo().set_param(
            "web.base.url", "http://test.local"
        )
        self.collection._compute_url()
        self.assertEqual(
            self.collection.url,
            f"http://test.local/.dav/{self.env.user.login}/{self.collection.id}",
        )

        self.env["ir.config_parameter"].sudo().set_param("web.base.url", "")
        self.collection._compute_url()
        self.assertEqual(
            self.collection.url,
            f"/.dav/{self.env.user.login}/{self.collection.id}",
        )

        self.assertIsNone(self.collection._odoo_to_http_datetime(False))
        self.assertEqual(self.collection._split_path("/a//b/c/"), ["a", "b", "c"])

    def test_dav_strip_extension_and_invalid_record_lookup(self):
        """Verify DAV href extension stripping and invalid ID handling."""
        from ..models.dav_collection import _dav_strip_item_extension

        self.assertEqual(_dav_strip_item_extension("abc.vcf"), "abc")
        self.assertEqual(_dav_strip_item_extension("abc.ics"), "abc")
        self.assertEqual(_dav_strip_item_extension("abc.txt"), "abc.txt")
        self.assertEqual(_dav_strip_item_extension(""), "")

        self.assertFalse(self.collection.get_record(["not-an-id"]))
        self.collection.field_uuid = self.env.ref("base.field_res_users__login")
        self.assertFalse(self.collection.get_record(["unknown-login"]))
        self.assertEqual(
            self.collection.get_record([f"{self.record.login}.ics"]),
            self.record,
        )

    def test_from_vobject_guards_and_eval_context(self):
        """Verify unsupported vobject structures and eval helpers."""
        self.assertIn("user", self.collection._eval_context())
        self.assertEqual(self.collection._eval_domain(), [])

        bogus = mock.Mock()
        bogus.name = "VCARD"
        self.collection.dav_type = "calendar"
        self.assertIsNone(self.collection.from_vobject(bogus))

        bogus.name = "VCALENDAR"
        if hasattr(bogus, "vevent"):
            del bogus.vevent
        self.assertIsNone(self.collection.from_vobject(bogus))

        self.collection.dav_type = "addressbook"
        bogus.name = "VCALENDAR"
        self.assertIsNone(self.collection.from_vobject(bogus))

        self.collection.dav_type = "files"
        self.assertIsNone(self.collection.from_vobject(bogus))
        self.assertIsNone(self.collection.to_vobject(self.record))

    def test_domain_validation_and_access_error_on_upload_outside_domain(self):
        """
        Verify invalid domain eval is rejected and
        upload outside domain raises AccessError.
        """

        bad_collection = self.env["dav.collection"].new(
            {
                "name": "Bad Domain",
                "dav_type": "calendar",
                "model_id": self.env.ref("base.model_res_users").id,
                "domain": "[",
            }
        )
        with self.assertRaises(SyntaxError):
            bad_collection._eval_domain()

        partner = self.env["res.partner"].create(
            {
                "name": "DAV Restricted Partner",
                "email": "restricted@example.com",
            }
        )
        source_collection = self.env["dav.collection"].create(
            {
                "name": "Source Partner Collection",
                "dav_type": "addressbook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "domain": f"[('id', '=', {partner.id})]",
            }
        )
        self.env["dav.collection.field_mapping"].create(
            {
                "collection_id": source_collection.id,
                "name": "FN",
                "field_id": self.env["ir.model.fields"]._get("res.partner", "name").id,
                "mapping_type": "simple",
            }
        )
        self.env["dav.collection.field_mapping"].create(
            {
                "collection_id": source_collection.id,
                "name": "EMAIL",
                "field_id": self.env["ir.model.fields"]._get("res.partner", "email").id,
                "mapping_type": "simple",
            }
        )

        restricted_collection = self.env["dav.collection"].create(
            {
                "name": "Restricted Partner Collection",
                "dav_type": "addressbook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "domain": "[('id', '=', -1)]",
            }
        )
        self.env["dav.collection.field_mapping"].create(
            {
                "collection_id": restricted_collection.id,
                "name": "FN",
                "field_id": self.env["ir.model.fields"]._get("res.partner", "name").id,
                "mapping_type": "simple",
            }
        )
        self.env["dav.collection.field_mapping"].create(
            {
                "collection_id": restricted_collection.id,
                "name": "EMAIL",
                "field_id": self.env["ir.model.fields"]._get("res.partner", "email").id,
                "mapping_type": "simple",
            }
        )

        vobj = source_collection.to_vobject(partner)

        with self.assertRaises(AccessError):
            restricted_collection.dav_upload(mock.Mock(), "/x", vobj)
