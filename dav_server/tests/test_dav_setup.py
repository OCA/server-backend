# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Checks for the self-service DAV details on the user preferences form."""

from odoo.tests.common import TransactionCase


class TestDavSetup(TransactionCase):
    def test_computed_connection_details(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "web.base.url", "https://odoo.example.test/"
        )
        user = self.env["res.users"].create(
            {
                "name": "DAV Setup Tester",
                "login": "dav+setup@example.test",
            }
        )
        self.assertEqual(user.dav_server_url, "https://odoo.example.test/dav/")
        self.assertEqual(user.dav_username, "dav+setup@example.test")
        self.assertEqual(
            user.dav_caldav_url,
            "https://odoo.example.test/dav/caldav/dav%2Bsetup%40example.test/",
        )
        self.assertEqual(
            user.dav_carddav_url,
            "https://odoo.example.test/dav/carddav/dav%2Bsetup%40example.test/",
        )

    def test_no_base_url_gives_empty_urls(self):
        self.env["ir.config_parameter"].sudo().set_param("web.base.url", "")
        user = self.env["res.users"].create(
            {"name": "DAV Setup No URL", "login": "dav-nourl"}
        )
        self.assertFalse(user.dav_server_url)
        self.assertFalse(user.dav_caldav_url)
        self.assertFalse(user.dav_carddav_url)
