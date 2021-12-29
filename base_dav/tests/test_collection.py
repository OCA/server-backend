# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from unittest import mock

from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

from ..radicale.collection import Storage


class TestCalendar(TransactionCase):
    def setUp(self):
        super().setUp()

        self.collection = self.env["dav.collection"].create({
            "name": "Test Collection",
            "dav_type": "calendar",
            "model_id": self.env.ref("base.model_res_users").id,
            "domain": "[]",
        })

        self.collection_partner = self.env["dav.collection"].create({
            "name": "Test Collection",
            "dav_type": "calendar",
            "model_id": self.env.ref("base.model_res_partner").id,
            "domain": "[]",
        })
        self.create_field_mapping(
            "login", "base.field_res_users__login",
            excode="result = record.login",
            imcode="result = item.value",
        )
        self.create_field_mapping(
            "name", "base.field_res_users__name",
        )
        self.create_field_mapping(
            "dtstart", "base.field_res_users__create_date",
        )
        self.create_field_mapping(
            "dtend", "base.field_res_users__write_date",
        )
        self.create_field_mapping_partner(
            "dtstart", "base.field_res_partner__date",
        )

        self.create_field_mapping_partner(
            "dtend", "base.field_res_partner__date",
        )
        self.create_field_mapping(
            "name", "base.field_res_partner__name",
        )
        start = datetime.now()
        stop = start + timedelta(hours=1)
        self.record = self.env["res.users"].create({
            "login": "tester",
            "name": "Test User",
            "create_date": start.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "write_date": stop.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        })
        self.partner_record = self.env['res.partner'].create({
            'date': '2011-04-30',
            'name': 'Test partner',
        })

    def create_field_mapping(self, name, field_ref, imcode=None, excode=None):
        return self.env["dav.collection.field_mapping"].create({
            "collection_id": self.collection.id,
            "name": name,
            "field_id": self.env.ref(field_ref).id,
            "mapping_type": "code" if imcode or excode else "simple",
            "import_code": imcode,
            "export_code": excode,
        })

    def create_field_mapping_partner(self, name, field_ref, imcode=None, excode=None):
        return self.env["dav.collection.field_mapping"].create({
            "collection_id": self.collection_partner.id,
            "name": name,
            "field_id": self.env.ref(field_ref).id,
            "mapping_type": "code" if imcode or excode else "simple",
            "import_code": imcode,
            "export_code": excode,
        })

    def compare_record(self, vobj, rec=None):
        tmp = self.collection.from_vobject(vobj)

        self.assertEqual((rec or self.record).login, tmp["login"])
        self.assertEqual((rec or self.record).name, tmp["name"])
        self.assertEqual((rec or self.record).create_date.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT), tmp["create_date"]
        )
        self.assertEqual((rec or self.record).write_date.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT), tmp["write_date"]
        )

    def compare_record_partner(self, vobj, rec=None):
        tmp = self.collection_partner.from_vobject(vobj)

        self.assertEqual((rec or self.partner_record).date.strftime(
            DEFAULT_SERVER_DATE_FORMAT), tmp["date"]
        )

    def test_import_export(self):
        # Exporting and importing should result in the same record
        vobj = self.collection.to_vobject(self.record)
        self.compare_record(vobj)

    def test_import_export_partner(self):
        # Exporting and importing should result in the same record
        vobj = self.collection_partner.to_vobject(self.partner_record)
        self.compare_record_partner(vobj)

    def test_from_vobject_bad_name(self):
        vobj = self.collection_partner.to_vobject(self.partner_record)
        vobj.name = 'FAKE'
        self.assertFalse(self.collection_partner.from_vobject(vobj))

    def test_from_vobject_has_not_vevent(self):
        vobj = self.collection_partner.to_vobject(self.partner_record)
        delattr(vobj, 'vevent')
        self.assertFalse(self.collection_partner.from_vobject(vobj))

    def test_from_vobject_bad_vcard(self):
        vobj = self.collection_partner.to_vobject(self.partner_record)
        self.collection_partner.dav_type = 'addressbook'
        vobj.name = 'FAKE'
        self.assertFalse(self.collection_partner.from_vobject(vobj))

    def test_from_vobject_missing_field(self):
        vobj = self.collection.to_vobject(self.record)
        children = list(next(vobj.getChildren()).getChildren())
        dtstart = next(e for e in children if e.name.lower() == 'dtstart')
        vevent = list(vobj.getChildren())[0]
        vevent.remove(dtstart)
        tmp = self.collection.from_vobject(vobj)
        self.assertNotIn('create_date', tmp)
        self.assertIn('name', tmp)
        self.assertIn('login', tmp)
        self.assertIn('write_date', tmp)

    def test_get_record(self):
        rec = self.collection.get_record([self.record.id])
        self.assertEqual(rec, self.record)

        self.collection.field_uuid = self.env.ref(
            "base.field_res_users__login",
        ).id
        rec = self.collection.get_record([self.record.login])
        self.assertEqual(rec, self.record)

    @mock.patch("odoo.addons.base_dav.radicale.collection.request")
    def test_collection(self, request_mock):
        request_mock.env = self.env
        collection_url = "/%s/%s" % (self.env.user.login, self.collection.id)
        collection = list(Storage.discover(collection_url))[0]

        # Try to get the test record
        record_url = "%s/%s" % (collection_url, self.record.id)
        self.assertIn(record_url, [c.href for c in collection.get_all()])

        # Get the test record using the URL and compare it
        items = collection.get_multi([record_url])
        item = items[0]
        self.compare_record(item._vobject_item)
        self.assertEqual(item.href, record_url)

        # Get a non-existing record
        self.assertFalse(collection.get_multi([record_url + "0"])[0])

        # Get the record and alter it later
        item = self.collection.to_vobject(self.record)
        self.record.login = "different"
        with self.assertRaises(AssertionError):
            self.compare_record(item)

        # Restore the record
        item = collection.upload(record_url, item)
        self.compare_record(item._vobject_item)

        # Delete an record
        collection.delete(item.href)
        self.assertFalse(self.record.exists())

        # Create a new record
        item = collection.upload(record_url + "0", item._vobject_item)
        record = self.collection.get_record(collection._split_path(item.href))
        self.assertNotEqual(record, self.record)
        self.compare_record(item._vobject_item, record)
