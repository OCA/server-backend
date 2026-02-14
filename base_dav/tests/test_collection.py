# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest import mock

import odoo.http as http
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

        # created_item.href can differ from requested href (Odoo assigns new id)
        vobj = created_item.vobject_item
        uid_value = ""
        if getattr(vobj, "uid", None):
            uid_value = vobj.uid.value or ""
        elif getattr(vobj, "vevent", None) and getattr(vobj.vevent, "uid", None):
            uid_value = vobj.vevent.uid.value or ""
        elif (
            getattr(vobj, "vevent_list", None)
            and vobj.vevent_list
            and getattr(vobj.vevent_list[0], "uid", None)
        ):
            uid_value = vobj.vevent_list[0].uid.value or ""
        self.assertIn(",", uid_value, "Expected UID in format '<model>,<id>'")
        _created_model, created_id_str = uid_value.split(",", 1)
        created_id = int(created_id_str)
        new_record = (
            self.env[self.collection.model_id.model].browse(created_id).exists()
        )
        self.assertTrue(new_record)
        self.assertNotEqual(new_record, self.record)
        self._compare_record(created_item.vobject_item, new_record)
