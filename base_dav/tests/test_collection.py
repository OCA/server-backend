# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from unittest import mock

from odoo.tests.common import TransactionCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

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
            "login", "base.field_res_users_login",
            excode="result = record.login",
            imcode="result = item.value",
        )
        self.create_field_mapping(
            "name", "base.field_res_users_name",
        )
        self.create_field_mapping(
            "dtstart", "base.field_res_users_create_date",
        )
        self.create_field_mapping(
            "dtend", "base.field_res_users_write_date",
        )

        start = datetime.now()
        stop = start + timedelta(hours=1)
        self.record = self.env["res.users"].create({
            "login": "tester",
            "name": "Test User",
            "create_date": start.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            "write_date": stop.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
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

    def compare_record(self, vobj, rec=None):
        tmp = self.collection.from_vobject(vobj)

        self.assertEqual((rec or self.record).login, tmp["login"])
        self.assertEqual((rec or self.record).name, tmp["name"])
        self.assertEqual((rec or self.record).create_date, tmp["create_date"])
        self.assertEqual((rec or self.record).write_date, tmp["write_date"])

    def test_import_export(self):
        # Exporting and importing should result in the same record
        vobj = self.collection.to_vobject(self.record)
        self.compare_record(vobj)

    def test_get_record(self):
        rec = self.collection.get_record([self.record.id])
        self.assertEqual(rec, self.record)

        self.collection.field_uuid = self.env.ref(
            "base.field_res_users_login",
        ).id
        rec = self.collection.get_record([self.record.login])
        self.assertEqual(rec, self.record)

    @mock.patch("odoo.addons.base_dav.radicale.collection.request")
    def test_collection(self, request_mock):
        request_mock.env = self.env
        collection_url = "/%s/%s" % (self.env.user.login, self.collection.id)
        collection = list(Collection.discover(collection_url))[0]

        # Try to get the test record
        record_url = "%s/%s" % (collection_url, self.record.id)
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
