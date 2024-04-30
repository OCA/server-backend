# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import http
from odoo.addons.website.controllers.main import Website


class Home(Website):
    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        result = super().web_login()
        if getattr(result, 'status_code', None) == 303 and result.location == '/my':
            if http.request.env['res.users'].browse(
                    http.request.uid
            ).has_group('user_group_readonly.group_readonly'):
                result.location = b'/web?' + http.request.httprequest.query_string
        return result
