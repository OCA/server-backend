# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http

from odoo.addons.web.controllers.home import Home


class HomeExtended(Home):
    @http.route()
    def web_load_menus(self, unique):
        response = super().web_load_menus(unique)
        # On logout & re-login we could see wrong menus being rendered
        # To avoid this, menu http cache must be disabled
        response.headers.remove("Cache-Control")
        return response
