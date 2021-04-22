# Copyright 2020 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from io import BytesIO

from odoo.tests.common import TransactionCase


class TestMockServer(TransactionCase):
    """Test MockServer."""

    def setUp(self):
        super().setUp()
        system_model = self.env["external.system"]
        self.system = system_model.create(
            {
                "name": "Mock FTP Server for testing",
                "system_type": "mock.ftp.system.adapter",
                "host": "example.acme.com",
                "username": "anonymous",
                "password": "secret",
                "state": "draft",
            }
        )
        path_model = self.env["external.system.path"]
        self.path = path_model.create(
            {
                "name": "Mock FTP Folder",
                "system_id": self.system.id,
                "remote_path": "example_directory",
            }
        )

    def test_mock_system(self):
        """Test Mock FTP Server."""
        path = self.path
        with path.client() as directory:
            system = path.system_id
            system.action_test_connection()
            self.assertEqual(system.state, "done")
            self.assertEqual(directory.listdir(), [])
            datas = BytesIO()
            datas.write(b"Hello World!")
            directory.putfo(datas, "hello.txt")
            self.assertEqual(directory.listdir(), ["hello.txt"])
            self.assertTrue(directory.exists("hello.txt"))
            self.assertFalse(directory.exists("bye.txt"))
            get_datas = BytesIO()
            directory.getfo("hello.txt", get_datas)
            get_datas.seek(0)
            hello_bytes = get_datas.read()
            self.assertEqual(hello_bytes, b"Hello World!")
            directory.remove("hello.txt")
            self.assertFalse(directory.exists("hello.txt"))
            self.assertEqual(directory.listdir(), [])
