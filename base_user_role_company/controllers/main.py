# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http

from odoo.addons.web.controllers.home import Home


class HomeExtended(Home):
    @http.route()
    def web_load_menus(self, lang=None):
        # v19 signature: (lang=None). Keep behavior of disabling menu HTTP cache.
        response = super().web_load_menus(lang=lang)
        # Avoid bare except-pass: remove header defensively
        if "Cache-Control" in response.headers:
            # Werkzeug Headers behaves like a dict for deletion
            del response.headers["Cache-Control"]
        return response
