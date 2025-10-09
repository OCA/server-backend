# Copyright 2026 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import HttpCase


class LoadMenusTests(HttpCase):
    def setUp(self):
        super().setUp()
        self.authenticate("admin", "admin")

    def test_load_menus(self):
        "Expect no errors on HomeExtended.web_load_menus controller"
        self.url_open("/web/webclient/load_menus")
