# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from types import SimpleNamespace

from odoo import http
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base_dav.radicale.collection import Collection


@tagged("post_install", "-at_install")
class TestDavCollectionFiles(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "DAV Files Partner",
                "email": "files@example.com",
            }
        )
        cls.files_collection = cls.env["dav.collection"].create(
            {
                "name": "Partner Files",
                "dav_type": "files",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "domain": f"[('id', '=', {cls.partner.id})]",
            }
        )
        cls.attachment = cls.env["ir.attachment"].create(
            {
                "name": "hello world.txt",
                "type": "binary",
                "datas": base64.b64encode(b"Hello DAV files").decode(),
                "res_model": "res.partner",
                "res_id": cls.partner.id,
                "mimetype": "text/plain",
            }
        )

    def setUp(self):
        super().setUp()
        req = SimpleNamespace(env=self.env, uid=self.env.uid)
        http._request_stack.push(req)
        self.addCleanup(http._request_stack.pop)

    def test_dav_list_returns_folders_for_files_collection(self):
        collection = Collection(f"{self.env.user.login}/{self.files_collection.id}")

        hrefs = list(collection.list())

        self.assertEqual(len(hrefs), 1)
        self.assertEqual(hrefs[0], self.partner.display_name.replace(" ", "+"))

    def test_dav_list_returns_attachments_in_folder(self):
        folder_href = self.partner.display_name.replace(" ", "+")
        hrefs = self.files_collection.dav_list(
            collection=Collection(f"{self.env.user.login}/{self.files_collection.id}"),
            path_components=[
                self.env.user.login,
                str(self.files_collection.id),
                folder_href,
            ],
        )

        self.assertEqual(len(hrefs), 1)
        self.assertIn("hello+world.txt", hrefs[0])

    def test_dav_get_returns_folder_wrapper_for_folder_href(self):
        collection = Collection(f"{self.env.user.login}/{self.files_collection.id}")
        folder_href = self.partner.display_name.replace(" ", "+")

        result = collection.get(folder_href)

        self.assertTrue(result)
        self.assertEqual(
            result.path,
            f"{self.env.user.login}/{self.files_collection.id}/{folder_href}",
        )

    def test_dav_get_returns_file_item_for_existing_attachment(self):
        collection = Collection(f"{self.env.user.login}/{self.files_collection.id}")
        folder_href = self.partner.display_name.replace(" ", "+")
        file_href = f"{folder_href}/hello+world.txt"

        result = collection.get(file_href)

        self.assertTrue(result)
        self.assertEqual(result.href, file_href)
        self.assertTrue(result.last_modified.endswith("GMT"))
        self.assertEqual(result.__class__.__name__, "FileItem")

    def test_dav_get_returns_none_for_missing_attachment(self):
        collection = Collection(f"{self.env.user.login}/{self.files_collection.id}")
        folder_href = self.partner.display_name.replace(" ", "+")
        file_href = f"{folder_href}/missing.txt"

        self.assertIsNone(collection.get(file_href))

    def test_dav_delete_is_noop_for_files_collection(self):
        collection = Collection(f"{self.env.user.login}/{self.files_collection.id}")
        folder_href = self.partner.display_name.replace(" ", "+")
        file_href = f"{folder_href}/hello+world.txt"

        collection.delete(file_href)

        self.assertTrue(self.attachment.exists())

    def test_dav_upload_returns_none_for_files_collection(self):
        collection = Collection(f"{self.env.user.login}/{self.files_collection.id}")
        folder_href = self.partner.display_name.replace(" ", "+")
        file_href = f"{folder_href}/hello+world.txt"

        uploaded, previous = collection.upload(file_href, object())

        self.assertIsNone(uploaded)
        self.assertTrue(previous)

    def test_dav_list_returns_empty_for_non_files_nested_path(self):
        calendar_collection = self.env["dav.collection"].create(
            {
                "name": "Nested Calendar Guard",
                "dav_type": "calendar",
                "model_id": self.env.ref("base.model_res_partner").id,
                "domain": f"[('id', '=', {self.partner.id})]",
            }
        )

        result = calendar_collection.dav_list(
            collection=Collection(f"{self.env.user.login}/{calendar_collection.id}"),
            path_components=[
                self.env.user.login,
                str(calendar_collection.id),
                "nested",
            ],
        )

        self.assertEqual(result, [])
