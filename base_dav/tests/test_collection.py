# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from unittest import mock

from odoo import fields
from odoo.tests.common import TransactionCase

from ..radicale.collection import Collection


class TestCalendar(TransactionCase):
    def setUp(self):
        super().setUp()

        self.collection = self.env["dav.collection"].create({
            "name": "Test Collection",
            "dav_type": "calendar",
            "model_id": self.env.ref("base.model_res_users").id,
            "domain": "[]",
        })

        self.create_field_mapping(
            "login", "res.users", "login",
            excode="result = record.login",
            imcode="result = item.value",
        )
        self.create_field_mapping(
            "name", "res.users", "name",
        )
        self.create_field_mapping(
            "dtstart", "res.users", "create_date",
        )
        self.create_field_mapping(
            "dtend", "res.users", "write_date",
        )

        self.record = self.env["res.users"].create({
            "login": "tester",
            "name": "Test User",
        })

    def create_field_mapping(
        self, name, model_name, field_name, imcode=None, excode=None
    ):
        field_id = self.env["ir.model.fields"].search([
            ("model", "=", model_name),
            ("name", "=", field_name),
        ], limit=1).id
        return self.env["dav.collection.field_mapping"].create({
            "collection_id": self.collection.id,
            "name": name,
            "field_id": field_id,
            "mapping_type": "code" if imcode or excode else "simple",
            "import_code": imcode,
            "export_code": excode,
        })

    def _normalize_dt(self, value):
        dt_val = fields.Datetime.to_datetime(value)
        return dt_val.replace(microsecond=0) if dt_val else dt_val

    def compare_record(self, vobj, rec=None):
        tmp = self.collection.from_vobject(vobj)

        self.assertEqual((rec or self.record).login, tmp["login"])
        self.assertEqual((rec or self.record).name, tmp["name"])
        self.assertEqual(
            self._normalize_dt((rec or self.record).create_date),
            self._normalize_dt(tmp["create_date"]),
        )
        self.assertEqual(
            self._normalize_dt((rec or self.record).write_date),
            self._normalize_dt(tmp["write_date"]),
        )

    def test_import_export(self):
        # Exporting and importing should result in the same record
        vobj = self.collection.to_vobject(self.record)
        self.compare_record(vobj)

    def test_get_record(self):
        rec = self.collection.get_record([self.record.id])
        self.assertEqual(rec, self.record)

        self.collection.field_uuid = self.env["ir.model.fields"].search([
            ("model", "=", "res.users"),
            ("name", "=", "login"),
        ], limit=1).id
        rec = self.collection.get_record([self.record.login])
        self.assertEqual(rec, self.record)

    def test_collection(self):
        from ..radicale import collection as radicale_collection
        original_request = radicale_collection.request
        radicale_collection.request = mock.Mock()
        self.addCleanup(
            setattr, radicale_collection, "request", original_request
        )
        radicale_collection.request.env = self.env
        collection_url = f"/{self.env.user.login}/{self.collection.id}"
        collection = list(Collection.discover(collection_url))[0]

        # Try to get the test record
        record_url = f"{collection_url}/{self.record.id}"
        self.assertIn(record_url, collection.list())

        # Get the test record using the URL and compare it
        item = collection.get(record_url)
        self.compare_record(item.item)
        self.assertEqual(item.href, record_url)

        # Get a non-existing record
        self.assertFalse(collection.get(record_url + "0"))

        # Get the record and alter it later
        item = self.collection.to_vobject(self.record)
        self.record.login = "different"
        with self.assertRaises(AssertionError):
            self.compare_record(item)

        # Restore the record
        item = collection.upload(record_url, item)
        self.compare_record(item.item)

        # Delete an record
        collection.delete(item.href)
        self.assertFalse(self.record.exists())

        # Create a new record
        item = collection.upload(record_url + "0", item)
        record = self.collection.get_record(collection._split_path(item.href))
        self.assertNotEqual(record, self.record)
        self.compare_record(item.item, record)


class TestAddressbookPhone(TransactionCase):
    def setUp(self):
        super().setUp()
        self.phone_number = "+15550000001"
        self.collection = self.env["dav.collection"].create({
            "name": "Contacts",
            "dav_type": "addressbook",
            "model_id": self.env.ref("base.model_res_partner").id,
            "domain": "[]",
        })
        self.create_field_mapping("TEL", "res.partner", "phone")
        self.record = self.env["res.partner"].create({
            "name": "Test Contact",
            "phone": self.phone_number,
        })

    def create_field_mapping(self, name, model_name, field_name):
        field_id = self.env["ir.model.fields"].search([
            ("model", "=", model_name),
            ("name", "=", field_name),
        ], limit=1).id
        return self.env["dav.collection.field_mapping"].create({
            "collection_id": self.collection.id,
            "name": name,
            "field_id": field_id,
            "mapping_type": "simple",
        })

    def test_addressbook_export_phone(self):
        vobj = self.collection.to_vobject(self.record)
        self.assertEqual(vobj.name, "VCARD")
        self.assertEqual(vobj.contents["version"][0].value, "4.0")
        self.assertEqual(vobj.contents["tel"][0].value, self.phone_number)

    def test_addressbook_import_phone(self):
        vobj = self.collection.to_vobject(self.record)
        data = self.collection.from_vobject(vobj)
        self.assertEqual(data.get("phone"), self.phone_number)


class TestAddressbookPhoneAndMobileExport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.phone_number = "+15550000001"
        self.mobile_number = "+15550000002"
        self.collection = self.env["dav.collection"].create({
            "name": "Contacts",
            "dav_type": "addressbook",
            "model_id": self.env.ref("base.model_res_partner").id,
            "domain": "[]",
        })
        self.create_field_mapping("TEL", "res.partner", "phone")
        self.create_field_mapping("TEL", "res.partner", "mobile")
        self.record = self.env["res.partner"].create({
            "name": "Test Contact",
            "phone": self.phone_number,
            "mobile": self.mobile_number,
        })

    def create_field_mapping(self, name, model_name, field_name):
        field_id = self.env["ir.model.fields"].search([
            ("model", "=", model_name),
            ("name", "=", field_name),
        ], limit=1).id
        return self.env["dav.collection.field_mapping"].create({
            "collection_id": self.collection.id,
            "name": name,
            "field_id": field_id,
            "mapping_type": "simple",
        })

    def test_addressbook_export_phone_and_mobile_as_tel(self):
        vobj = self.collection.to_vobject(self.record)
        tel_values = [entry.value for entry in vobj.contents.get("tel", [])]
        self.assertIn(self.phone_number, tel_values)
        self.assertIn(self.mobile_number, tel_values)
        self.assertEqual(len(tel_values), 2)
