# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import datetime
from types import SimpleNamespace

import vobject
from dateutil import tz

from odoo.tests import tagged

from .common import BaseDavTestCase


@tagged("post_install", "-at_install")
class TestDavCollectionFieldMapping(BaseDavTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.create_partner(
            name="John Doe",
            email="john@example.com",
        )
        fixture = cls.create_partner_addressbook_fixture(
            partner=cls.partner,
            name="Address Book",
        )
        cls.collection = fixture.collection
        cls.map_name = fixture.mappings["name"]
        cls.map_email = fixture.mappings["email"]

        cls.map_code = cls.add_mapping(
            cls.collection,
            name="X-CUSTOM",
            field_xmlid="base.field_res_partner__name",
            import_code="result = (item.value or '').upper()",
            export_code="result = (record.name or '').lower()",
        )
        cls.map_binary = cls.add_mapping(
            cls.collection,
            name="PHOTO",
            field_xmlid="base.field_res_partner__image_1920",
        )
        cls.map_n = cls.add_mapping(
            cls.collection,
            name="N",
            field_xmlid="base.field_res_partner__name",
        )

    def test_from_vobject_simple_and_code(self):
        card = vobject.vCard()
        card.add("fn").value = "Jane"
        card.add("email").value = "jane@example.com"
        card.add("x-custom").value = "abc"

        self.assertEqual(self.map_name.from_vobject(card.fn), "Jane")
        self.assertEqual(self.map_email.from_vobject(card.email), "jane@example.com")
        self.assertEqual(
            self.map_code.from_vobject(card.contents["x-custom"][0]), "ABC"
        )

    def test_to_vobject_simple_and_code(self):
        self.assertEqual(self.map_name.to_vobject(self.partner), "John Doe")
        self.assertEqual(self.map_email.to_vobject(self.partner), "john@example.com")
        self.assertEqual(self.map_code.to_vobject(self.partner), "john doe")

    def test_to_vobject_false_returns_none(self):
        partner = self.create_partner(name="No Email", email=False)
        self.assertIsNone(self.map_email.to_vobject(partner))

    def test_datetime_helpers(self):
        aware_dt = datetime.datetime(
            2024, 1, 2, 12, 30, 0, tzinfo=tz.gettz("Europe/Kyiv")
        )
        item_dt = SimpleNamespace(value=aware_dt)
        item_date = SimpleNamespace(value=datetime.date(2024, 1, 2))
        item_other = SimpleNamespace(value="bad")

        dt_as_odoo = self.map_name._from_vobject_datetime(item_dt)
        self.assertEqual(dt_as_odoo, "2024-01-02 10:30:00")
        self.assertEqual(
            self.map_name._from_vobject_datetime(item_date),
            "2024-01-02 00:00:00",
        )
        self.assertIsNone(self.map_name._from_vobject_datetime(item_other))

        self.assertEqual(self.map_name._from_vobject_date(item_dt), "2024-01-02")
        self.assertEqual(self.map_name._from_vobject_date(item_date), "2024-01-02")
        self.assertIsNone(self.map_name._from_vobject_date(item_other))

    def test_to_vobject_datetime_helpers(self):
        naive_dt = datetime.datetime(2024, 1, 2, 12, 30, 0)
        aware = self.map_name._to_vobject_datetime("2024-01-02 12:30:00")
        self.assertEqual(aware.tzinfo, tz.UTC)
        dt_value = datetime.datetime(2024, 1, 2, 12, 30, 0)
        self.assertEqual(
            self.map_name._to_vobject_datetime_rev(dt_value),
            "20240102T123000Z",
        )
        self.assertEqual(
            self.map_name._to_vobject_date("2024-01-02"),
            datetime.date(2024, 1, 2),
        )

        result = self.map_name.to_vobject(self.env["res.partner"].new({"name": "Tmp"}))
        self.assertEqual(result, "Tmp")

        self.assertEqual(
            self.map_name._to_vobject_datetime(naive_dt).tzinfo,
            tz.UTC,
        )

    def test_binary_helpers(self):
        raw_jpeg = b"\xff\xd8\xffabc"
        encoded = self.map_binary._from_vobject_binary(SimpleNamespace(value=raw_jpeg))
        self.assertEqual(base64.b64decode(encoded), raw_jpeg)

        valid_b64 = base64.b64encode(b"hello-world").decode("ascii")
        reencoded = self.map_binary._from_vobject_binary(
            SimpleNamespace(value=valid_b64)
        )
        self.assertEqual(base64.b64decode(reencoded), b"hello-world")

        invalid_b64 = self.map_binary._from_vobject_binary(SimpleNamespace(value="%%%"))
        self.assertEqual(base64.b64decode(invalid_b64), b"%%%")

        self.assertIsNone(
            self.map_binary._from_vobject_binary(SimpleNamespace(value=""))
        )
        self.assertEqual(
            self.map_binary._to_vobject_binary(base64.b64encode(b"abc")),
            base64.b64encode(b"abc").decode("ascii"),
        )

    def test_name_helpers(self):
        name_obj = vobject.vcard.Name(family="Doe")
        self.assertEqual(
            self.map_n._from_vobject_char_n(SimpleNamespace(value=name_obj)),
            "Doe",
        )
        self.assertEqual(
            self.map_n._from_vobject_char_n(SimpleNamespace(value="Doe;John")),
            "Doe",
        )
        self.assertIsNone(self.map_n._from_vobject_char_n(SimpleNamespace(value=None)))

        converted = self.map_n._to_vobject_char_n("Doe")
        self.assertEqual(converted.family, "Doe")

    def test_simple_fallback_and_bool_conversion_paths(self):
        """Verify simple mapping fallback branches."""
        note_field = self.env["ir.model.fields"]._get("res.partner", "comment")
        mapping = self.env["dav.collection.field_mapping"].create(
            {
                "collection_id": self.collection.id,
                "name": "NOTE",
                "mapping_type": "simple",
                "field_id": note_field.id,
            }
        )

        child = SimpleNamespace(value="Some note")
        self.assertEqual(mapping.from_vobject(child), "Some note")

        partner = self.create_partner(
            name="Bool Test",
            email=False,
            comment=False,
        )
        self.assertIsNone(mapping.to_vobject(partner))
