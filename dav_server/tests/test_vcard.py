# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import io

from PIL import Image

from odoo.tests import TransactionCase, tagged

from .. import vcard


@tagged("post_install", "-at_install")
class TestVCard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Ross Golder",
                "login": "vcard-tester",
                "email": "ross@example.com",
            }
        )
        cls.country = cls.env.ref("base.th")
        cls.category = cls.env["res.partner.category"].create({"name": "Address Book"})

    # ==================================================================
    # Export
    # ==================================================================
    def test_export_basic_contact(self):
        partner = self._partner()
        raw = vcard.partner_to_vcard(partner)
        self.assertTrue(raw.startswith("BEGIN:VCARD"))
        self.assertIn("VERSION:3.0", raw)
        self.assertIn(f"UID:{partner.dav_uid}", raw)
        self.assertIn("FN:Alice Smith", raw)
        self.assertIn("N:Smith;Alice;;;", raw)
        self.assertIn("EMAIL:alice@example.com", raw)
        self.assertIn("KIND:individual", raw)

    def test_export_company_is_kind_group(self):
        partner = self._partner(name="Acme Ltd", is_company=True)
        self.assertIn("KIND:group", vcard.partner_to_vcard(partner))

    def test_export_typed_telephone_numbers(self):
        partner = self._partner(phone="+66 2 123 4567", mobile="+66 81 234 5678")
        raw = vcard.partner_to_vcard(partner)
        self.assertIn("TEL;TYPE=WORK,VOICE:+66 2 123 4567", raw)
        self.assertIn("TEL;TYPE=CELL:+66 81 234 5678", raw)

    def test_export_categories_and_title(self):
        partner = self._partner(function="Physician")
        partner.category_id = [(4, self.category.id)]
        raw = vcard.partner_to_vcard(partner)
        self.assertIn("CATEGORIES:Address Book", raw)
        self.assertIn("TITLE:Physician", raw)

    def test_export_postal_address_uses_home_type_for_contact(self):
        partner = self._partner(
            street="123 Test Road", street2="Building B", zip="10330", city="Bangkok"
        )
        raw = vcard.partner_to_vcard(partner)
        self.assertIn(
            "ADR;TYPE=HOME:Building B;;123 Test Road;Bangkok;;10330;TH", raw
        )

    def test_export_postal_address_uses_work_type_for_invoice(self):
        partner = self._partner(type="invoice")
        raw = vcard.partner_to_vcard(partner)
        self.assertIn("ADR;TYPE=WORK:", raw)

    def test_export_organisation_from_parent(self):
        child = self.env["res.partner"].create(
            {
                "name": "Child",
                "email": "child@example.com",
                "parent_id": self.env["res.partner"]
                .create({"name": "Parent Co", "is_company": True})
                .id,
            }
        )
        self.assertIn("ORG:Parent Co", vcard.partner_to_vcard(child))

    def test_export_website_is_normalised(self):
        partner = self._partner(website="example.com")
        self.assertIn("URL:http://example.com", vcard.partner_to_vcard(partner))

    def test_export_embedded_photo(self):
        partner = self._partner()
        # Odoo's Image field stores base64 and validates the payload with PIL,
        # so the bytes have to be a genuinely decodable image.
        buffer = io.BytesIO()
        Image.new("RGB", (1, 1), (200, 30, 30)).save(buffer, format="PNG")
        partner.image_1920 = base64.b64encode(buffer.getvalue())
        raw = vcard.partner_to_vcard(partner)
        # Odoo re-encodes image_1920 to JPEG on write, so that is what the
        # sniffed TYPE parameter reports.
        self.assertIn("PHOTO;ENCODING=b;TYPE=JPEG:", raw)

    def test_thai_name_is_not_split_into_family_given(self):
        partner = self._partner(name="โรส โกลเดอร์")
        raw = vcard.partner_to_vcard(partner)
        self.assertIn("N:;โรส โกลเดอร์;;;", raw)

    # ==================================================================
    # Import
    # ==================================================================
    def test_import_basic_contact(self):
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\nUID:imported-1\r\n"
            "N:Doe;John;;;\r\nFN:John Doe\r\n"
            "EMAIL:john.doe@example.com\r\n"
            "TEL;TYPE=CELL:+66 81 000 1111\r\n"
            "TEL;TYPE=WORK,VOICE:+66 2 000 2222\r\n"
            "ORG:Example Ltd\r\nTITLE:Manager\r\n"
            "ADR;TYPE=HOME:;;1 Main St;Bangkok;;10100;TH\r\n"
            "URL:https://example.com\r\n"
            "CATEGORIES:Address Book,Friends\r\n"
            "NICKNAME:Johnny\r\nNOTE:Met at a conference\r\n"
            "END:VCARD\r\n"
        )
        values = vcard.vcard_to_partner_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["name"], "John Doe")
        self.assertEqual(values["email"], "john.doe@example.com")
        self.assertEqual(values["mobile"], "+66 81 000 1111")
        self.assertEqual(values["phone"], "+66 2 000 2222")
        self.assertEqual(values["company_name"], "Example Ltd")
        self.assertEqual(values["function"], "Manager")
        self.assertEqual(values["street"], "1 Main St")
        self.assertEqual(values["city"], "Bangkok")
        self.assertEqual(values["zip"], "10100")
        self.assertEqual(values["type"], "contact")
        self.assertEqual(values["website"], "example.com")
        self.assertEqual(values["ref"], "Johnny")
        self.assertEqual(values["comment"], "Met at a conference")
        self.assertEqual(values["category_id"][0][0], 6)
        self.assertEqual(len(values["category_id"][0][2]), 2)

    def test_import_group_kind_sets_is_company(self):
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\nUID:imported-2\r\n"
            "N:;;;;\r\nFN:Acme Ltd\r\nKIND:group\r\nEND:VCARD\r\n"
        )
        values = vcard.vcard_to_partner_values(payload.encode("utf-8"), self.user)
        self.assertTrue(values["is_company"])

    def test_import_work_address_sets_invoice_type(self):
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\nUID:imported-work\r\n"
            "N:;;;;\r\nFN:Corp\r\n"
            "ADR;TYPE=WORK:;;9 Other Rd;Chiang Mai;;50100;TH\r\n"
            "END:VCARD\r\n"
        )
        values = vcard.vcard_to_partner_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["type"], "invoice")
        self.assertEqual(values["street"], "9 Other Rd")

    def test_import_untyped_telephone_falls_back_to_work(self):
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\nUID:imported-notel\r\n"
            "N:;;;;\r\nFN:No Type\r\nTEL:+66 9 000 0000\r\nEND:VCARD\r\n"
        )
        values = vcard.vcard_to_partner_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["phone"], "+66 9 000 0000")

    def test_import_falls_back_to_structured_name(self):
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\nUID:imported-noname\r\n"
            "N:Curie;Marie;;;\r\nEND:VCARD\r\n"
        )
        values = vcard.vcard_to_partner_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["name"], "Marie Curie")

    def test_import_rejects_card_without_any_name(self):
        payload = b"BEGIN:VCARD\r\nVERSION:3.0\r\nUID:x\r\nEND:VCARD\r\n"
        with self.assertRaises(vcard.UnsupportedPayload):
            vcard.vcard_to_partner_values(payload, self.user)

    def test_import_rejects_garbage(self):
        with self.assertRaises(vcard.UnsupportedPayload):
            vcard.vcard_to_partner_values(b"this is not a vcard", self.user)

    def test_import_unknown_category_is_created(self):
        payload = (
            "BEGIN:VCARD\r\nVERSION:3.0\r\nUID:imported-3\r\n"
            "N:;;;;\r\nFN:Categorised\r\nCATEGORIES:Newly Invented\r\n"
            "END:VCARD\r\n"
        )
        values = vcard.vcard_to_partner_values(payload.encode("utf-8"), self.user)
        categories = self.env["res.partner.category"].browse(
            values["category_id"][0][2]
        )
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories.name, "Newly Invented")

    # ==================================================================
    # Round trip
    # ==================================================================
    def test_export_then_import_preserves_core_fields(self):
        partner = self._partner(
            phone="+66 2 111 2222",
            mobile="+66 81 333 4444",
            function="Engineer",
            street="9 Sukhumvit",
            city="Bangkok",
            zip="10110",
        )
        partner.category_id = [(4, self.category.id)]
        raw = vcard.partner_to_vcard(partner)
        values = vcard.vcard_to_partner_values(raw.encode("utf-8"), self.user)
        self.assertEqual(values["name"], partner.name)
        self.assertEqual(values["email"], partner.email)
        self.assertEqual(values["phone"], partner.phone)
        self.assertEqual(values["mobile"], partner.mobile)
        self.assertEqual(values["function"], partner.function)
        self.assertEqual(values["street"], partner.street)
        self.assertEqual(values["city"], partner.city)
        self.assertEqual(values["zip"], partner.zip)
        self.assertEqual(values["is_company"], partner.is_company)
        self.assertEqual(values["type"], partner.type)

    def _partner(self, **overrides):
        values = {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "street": "1 Test Road",
            "city": "Bangkok",
            "zip": "10330",
            "country_id": self.country.id,
            "type": "contact",
        }
        values.update(overrides)
        return self.env["res.partner"].create(values)