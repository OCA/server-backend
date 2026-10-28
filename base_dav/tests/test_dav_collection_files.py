# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from .common import BaseDavTestCase


@tagged("post_install", "-at_install")
class TestDavCollectionFiles(BaseDavTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        fixture = cls.create_files_fixture(
            partner=cls.create_partner(
                name="DAV Files Partner",
                email="files@example.com",
            ),
            collection_name="Partner Files",
            attachment_name="hello world.txt",
            attachment_raw=b"Hello DAV files",
            mimetype="text/plain",
        )
        cls.partner = fixture.partner
        cls.files_collection = fixture.collection
        cls.attachment = fixture.attachment

    def setUp(self):
        super().setUp()
        self.push_request_context()

    def _folder_href(self):
        """Return encoded folder href for the partner record."""
        return self.dav_quote(self.partner.display_name)

    def _file_href(self):
        """Return encoded file href for the linked attachment."""
        return f"{self._folder_href()}/{self.dav_quote(self.attachment.name)}"

    def test_dav_list_returns_folders_for_files_collection(self):
        """Verify files collection root lists record folders."""
        collection = self.make_collection(self.files_collection)

        hrefs = list(collection.list())

        self.assertEqual(len(hrefs), 1)
        self.assertEqual(hrefs[0], self._folder_href())

    def test_dav_list_returns_attachments_in_folder(self):
        """Verify files collection lists attachments inside record folder."""
        collection = self.make_collection(self.files_collection)

        hrefs = self.files_collection.dav_list(
            collection=collection,
            path_components=[
                self.env.user.login,
                str(self.files_collection.id),
                self._folder_href(),
            ],
        )

        self.assertEqual(len(hrefs), 1)
        self.assertIn(self.dav_quote(self.attachment.name), hrefs[0])

    def test_dav_get_returns_folder_wrapper_for_folder_href(self):
        collection = self.make_collection(self.files_collection)

        result = collection.get(self._folder_href())

        self.assertTrue(result)
        self.assertEqual(
            result.path,
            f"{self.env.user.login}/{self.files_collection.id}/{self._folder_href()}",
        )

    def test_dav_get_returns_file_item_for_existing_attachment(self):
        collection = self.make_collection(self.files_collection)

        result = collection.get(self._file_href())

        self.assertTrue(result)
        self.assertEqual(result.href, self._file_href())
        self.assertTrue(result.last_modified.endswith("GMT"))
        self.assertEqual(result.__class__.__name__, "FileItem")

    def test_dav_get_returns_none_for_missing_attachment(self):
        collection = self.make_collection(self.files_collection)
        missing_href = f"{self._folder_href()}/missing.txt"

        self.assertIsNone(collection.get(missing_href))

    def test_dav_delete_is_noop_for_files_collection(self):
        collection = self.make_collection(self.files_collection)

        collection.delete(self._file_href())

        self.assertTrue(self.attachment.exists())

    def test_dav_upload_returns_none_for_files_collection(self):
        collection = self.make_collection(self.files_collection)

        uploaded, previous = collection.upload(self._file_href(), object())

        self.assertIsNone(uploaded)
        self.assertTrue(previous)

    def test_dav_list_returns_empty_for_non_files_nested_path(self):
        calendar_collection = self.create_collection(
            name="Nested Calendar Guard",
            dav_type="calendar",
            model_xmlid="base.model_res_partner",
            domain=f"[('id', '=', {self.partner.id})]",
        )

        result = calendar_collection.dav_list(
            collection=self.make_collection(calendar_collection),
            path_components=[
                self.env.user.login,
                str(calendar_collection.id),
                "nested",
            ],
        )

        self.assertEqual(result, [])
