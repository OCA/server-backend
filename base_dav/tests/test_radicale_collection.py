# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace
from unittest import mock

from odoo import http
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base_dav.radicale.collection import (
    Collection,
    Storage,
    _abs_href,
    _norm_path,
    _rel_href,
)


@tagged("post_install", "-at_install")
class TestDavRadicaleCollection(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "DAV Partner",
                "email": "dav@example.com",
            }
        )
        cls.collection_record = cls.env["dav.collection"].create(
            {
                "name": "Contacts",
                "dav_type": "addressbook",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "domain": f"[('id', '=', {cls.partner.id})]",
            }
        )
        cls.env["dav.collection.field_mapping"].create(
            {
                "collection_id": cls.collection_record.id,
                "name": "FN",
                "mapping_type": "simple",
                "field_id": cls.env["ir.model.fields"]._get("res.partner", "name").id,
            }
        )
        cls.env["dav.collection.field_mapping"].create(
            {
                "collection_id": cls.collection_record.id,
                "name": "EMAIL",
                "mapping_type": "simple",
                "field_id": cls.env["ir.model.fields"]._get("res.partner", "email").id,
            }
        )

    def setUp(self):
        super().setUp()
        self.request_obj = SimpleNamespace(env=self.env, uid=self.env.uid)
        http._request_stack.push(self.request_obj)
        self.addCleanup(http._request_stack.pop)

    def test_path_helpers(self):
        self.assertEqual(_norm_path("/demo//x/"), "demo/x")
        self.assertEqual(_abs_href("user/7", "15"), "/user/7/15")
        self.assertEqual(_abs_href("user/7", "/user/7/15"), "/user/7/15")
        self.assertEqual(_rel_href("user/7", "/user/7/15"), "15")
        self.assertEqual(_rel_href("", "/abc"), "abc")

    def test_root_and_principal_listing(self):
        root = Collection("")
        self.assertIn(self.env.user.login, list(root.list()))

        principal = Collection(self.env.user.login)
        children = list(principal.list())
        self.assertIn(f"{self.env.user.login}/{self.collection_record.id}", children)

    def test_collection_list_get_and_get_multi(self):
        collection = Collection(f"{self.env.user.login}/{self.collection_record.id}")
        href = str(self.partner.id)

        listed = list(collection.list())
        self.assertIn(href, listed)

        item = collection.get(href)
        self.assertTrue(item)
        self.assertEqual(item.href, href)

        multi = list(collection.get_multi([href, href]))
        self.assertEqual(len(multi), 1)
        self.assertEqual(multi[0][0], href)
        self.assertTrue(multi[0][1])

    def test_collection_upload_delete_meta_and_last_modified(self):
        collection = Collection(f"{self.env.user.login}/{self.collection_record.id}")
        href = str(self.partner.id)

        old_item = collection.get(href)
        vobj = old_item.vobject_item
        vobj.email.value = "updated@example.com"

        uploaded, previous = collection.upload(href, vobj)
        self.assertTrue(uploaded)
        self.assertTrue(previous)
        self.partner.invalidate_recordset(["email"])
        self.assertEqual(self.partner.email, "updated@example.com")

        self.assertEqual(collection.get_meta(), {})
        self.assertEqual(collection.get_meta("tag"), "VADDRESSBOOK")
        self.assertEqual(
            collection.get_meta("D:displayname"),
            self.collection_record.display_name,
        )
        self.assertEqual(
            collection.get_meta("C:supported-calendar-component-set"),
            "VTODO,VEVENT,VJOURNAL",
        )
        self.assertEqual(collection.get_meta("ICAL:calendar-color"), "#48c9f4")
        self.assertTrue(collection.last_modified)

        collection.delete(href)
        self.assertFalse(self.partner.exists())

    def test_collection_upload_delete_guards(self):
        not_collection = Collection("unknown/path")
        with self.assertRaises(ValueError):
            not_collection.upload("1", SimpleNamespace())
        with self.assertRaises(ValueError):
            not_collection.delete("1")

        real_collection = Collection(
            f"{self.env.user.login}/{self.collection_record.id}"
        )
        with self.assertRaises(NotImplementedError):
            real_collection.delete()

    def test_storage_discover_and_guard_methods(self):
        storage = Storage(configuration=mock.Mock())
        collection_path = f"{self.env.user.login}/{self.collection_record.id}"
        item_path = f"{collection_path}/{self.partner.id}"

        zero = list(storage.discover(collection_path, depth="0"))
        self.assertEqual(len(zero), 1)
        self.assertIsInstance(zero[0], Collection)

        deep = list(storage.discover(collection_path, depth="1"))
        self.assertTrue(deep)
        self.assertEqual(deep[0].path, collection_path)

        item = list(storage.discover(item_path, depth="0"))
        self.assertEqual(len(item), 1)
        self.assertTrue(item[0])

        self.assertEqual(list(storage.discover(f"{self.env.user.login}/999999/1")), [])

        with self.assertRaises(NotImplementedError):
            storage.move(mock.Mock(), mock.Mock(), "x")
        with self.assertRaises(NotImplementedError):
            storage.create_collection("x")

        with storage.acquire_lock("r", user=self.env.user.login):
            pass

        self.assertTrue(Storage(configuration=mock.Mock()).verify())

    def test_collection_get_all_skips_missing_items(self):
        """Verify get_all skips empty items returned by get()."""
        collection = Collection(f"{self.env.user.login}/{self.collection_record.id}")

        with (
            mock.patch.object(
                collection,
                "list",
                return_value=["1", "2", "3"],
            ),
            mock.patch.object(
                collection,
                "get",
                side_effect=[object(), None, object()],
            ),
        ):
            items = list(collection.get_all())

        self.assertEqual(len(items), 2)

    def test_collection_get_meta_without_record(self):
        """Verify get_meta for non-collection path."""
        collection = Collection("unknown/path")

        self.assertIsNone(collection.get_meta("tag"))
        self.assertEqual(collection.get_meta(), {})
        self.assertEqual(collection.last_modified, "")

    def test_file_item_invalid_base64_is_handled(self):
        """Verify FileItem tolerates invalid attachment base64."""
        from ..radicale.collection import FileItem

        attachment = SimpleNamespace(datas="%%%")
        collection = Collection(f"{self.env.user.login}/{self.collection_record.id}")

        item = FileItem(
            collection=collection,
            href="bad.txt",
            attachment=attachment,
            last_modified="",
        )

        self.assertEqual(item.href, "bad.txt")
        self.assertEqual(item.last_modified, "")

    def test_storage_discover_root_and_principal_depth_one(self):
        """Verify discover returns child collections for root/principal paths."""
        storage = Storage(configuration=mock.Mock())

        root_items = list(storage.discover("", depth="1"))
        self.assertTrue(root_items)
        self.assertEqual(root_items[0].path, "")

        principal_items = list(storage.discover(self.env.user.login, depth="1"))
        self.assertTrue(principal_items)
        self.assertEqual(principal_items[0].path, self.env.user.login)
