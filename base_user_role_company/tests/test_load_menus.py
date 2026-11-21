# Copyright 2026 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# v20: The HomeExtended controller override was removed because
# web_load_menus already sets Cache-Control: no-store natively.
# This test just verifies the endpoint is reachable without errors.

from odoo.tests import common
from odoo.tests.common import HttpCase


class LoadMenusTests(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = common.new_test_user(
            cls.env,
            login="load_menus_test_user",
            password="load_menus_test_pass",
        )

    def setUp(self):
        super().setUp()
        self.authenticate("load_menus_test_user", "load_menus_test_pass")

    def test_load_menus(self):
        "Expect no errors on the web_load_menus endpoint"
        response = self.url_open("/web/webclient/load_menus")
        self.assertEqual(response.status_code, 200)
