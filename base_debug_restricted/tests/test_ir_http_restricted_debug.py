# Copyright 2026 QoQa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.web.tests.test_login import TestWebLoginCommon


@tagged("-at_install", "post_install")
class TestIrHttpRestrictedDebug(TestWebLoginCommon):
    @mute_logger("odoo.http")
    def test_debug_mode_restricted_public(self):
        """Test that debug mode is forbidden for public users"""
        response = self.url_open(
            "/web/reset_password?debug=1&self=test",
        )
        self.assertEqual(response.status_code, 500)
        # details of the traceback should not be shown to public users
        self.assertNotIn(
            "Traceback (most recent call last)",
            response.text,
            "Debug mode should be forbidden for public users",
        )

    @mute_logger("odoo.http")
    def test_debug_mode_restricted_user(self):
        """Test that debug mode is forbidden for users without the group"""
        self.login("internal_user", "internal_user")

        response = self.url_open(
            "/web/reset_password?debug=1&self=test",
        )
        self.assertEqual(response.status_code, 500)
        # details of the traceback should not be shown to unallowed users
        self.assertNotIn(
            "Traceback (most recent call last)",
            response.text,
            "Debug mode should be forbidden for users without the group",
        )

    @mute_logger("odoo.http")
    def test_debug_mode_allowed(self):
        """Test that debug mode is allowed for users with the group"""
        internal_user = self.env["res.users"].search(
            [("login", "=", "internal_user")], limit=1
        )
        internal_user.groups_id = [
            Command.link(self.env.ref("base_debug_restricted.group_debug_mode").id)
        ]

        self.login("internal_user", "internal_user")

        response = self.url_open(
            "/web/reset_password?debug=1&self=test",
        )
        self.assertEqual(response.status_code, 500)
        # details of the traceback should be shown to allowed users
        self.assertIn(
            "Traceback (most recent call last)",
            response.text,
            "Debug mode should be allowed for users with the group",
        )

    def test_debug_mode_backend_allowed(self):
        """Test that debug mode is allowed for users with the group in backend"""
        internal_user = self.env["res.users"].search(
            [("login", "=", "internal_user")], limit=1
        )
        internal_user.groups_id = [
            Command.link(self.env.ref("base_debug_restricted.group_debug_mode").id)
        ]

        self.login("internal_user", "internal_user")

        response = self.url_open(
            "/odoo?debug=1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '"debug": "1"',
            response.text,
            "Debug mode should be allowed for users with the group in backend",
        )

    def test_debug_mode_backend_restricted(self):
        """Test that debug mode is forbidden for users without the group in backend"""
        self.login("internal_user", "internal_user")

        response = self.url_open(
            "/odoo?debug=1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            '"debug": "1"',
            response.text,
            "Debug mode should be forbidden for users without the group in backend",
        )
