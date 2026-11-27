# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import BaseDavTestCase


@tagged("post_install", "-at_install")
class TestCalendar(BaseDavTestCase):
    @classmethod
    def setUpClass(cls):
        """Prepare shared calendar collection, mappings and record."""
        super().setUpClass()

        fixture = cls.create_users_calendar_fixture(
            name="Test Collection",
            domain="[]",
        )
        cls.collection = fixture.collection
        cls.record = fixture.record
        cls.map_login = fixture.mappings["login"]
        cls.map_name = fixture.mappings["name"]

    def setUp(self):
        """Push request context required by low-level DAV wrapper tests."""
        super().setUp()
        self.push_request_context()

    def _compare_record(self, vobj, rec=None):
        """Assert that imported vobject values match the expected record."""
        imported_vals = self.collection.from_vobject(vobj)
        expected_record = rec or self.record
        self.assertEqual(expected_record.login, imported_vals["login"])
        self.assertEqual(expected_record.name, imported_vals["name"])

    def test_import_export(self):
        """Verify export followed by import preserves record values."""
        vobj = self.collection.to_vobject(self.record)
        self._compare_record(vobj)

    def test_get_record(self):
        """Verify record lookup by ID and by custom UUID field."""
        record = self.collection.get_record([str(self.record.id)])
        self.assertEqual(record, self.record)

        self.collection.field_uuid = self.env.ref("base.field_res_users__login")
        record = self.collection.get_record([self.record.login])
        self.assertEqual(record, self.record)

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
        """Verify tag, URL and datetime helper methods."""
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
        """Verify DAV href extension stripping and invalid lookup handling."""
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
        """Verify invalid domains fail and upload outside domain is rejected."""
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

        partner = self.create_partner(
            name="DAV Restricted Partner",
            email="restricted@example.com",
        )

        source_fixture = self.create_partner_addressbook_fixture(
            partner=partner,
            name="Source Partner Collection",
        )
        source_collection = source_fixture.collection

        restricted_collection = self.create_collection(
            name="Restricted Partner Collection",
            dav_type="addressbook",
            model_xmlid="base.model_res_partner",
            domain="[('id', '=', -1)]",
        )
        self.add_mapping(
            restricted_collection,
            name="FN",
            field_xmlid="base.field_res_partner__name",
        )
        self.add_mapping(
            restricted_collection,
            name="EMAIL",
            field_xmlid="base.field_res_partner__email",
        )

        vobj = source_collection.to_vobject(partner)

        with self.assertRaises(AccessError):
            restricted_collection.dav_upload(mock.Mock(), "/x", vobj)
