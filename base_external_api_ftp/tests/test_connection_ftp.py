from odoo.tests.common import TransactionCase


class TestFTPConnection(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.ApicliConnection = self.env["apicli.connection"]
        self.demo_connection = self.ApicliConnection.get_by_code("DemoFTP")
        self.Partner = self.env["res.partner"]
        self.partner1 = self.Partner.search([])

    def test_connection(self):
        "Connection is confirmed"
        self.assertEqual(self.demo_connection.state, "confirmed")

    def test_upload_file_ftp(self):
        "tests the file upload"
        self.assertTrue(self.partner1.action_upload_partner_master)

    def test_delete_file_ftp(self):
        "tests the files deletion"
        self.assertTrue(self.demo_connection.cron_download_ftp_files)
