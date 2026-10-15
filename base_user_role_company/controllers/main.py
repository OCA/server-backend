# Copyright (C) 2022 Open Source Integrators# Copyright (C) 2026 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.home import Home


class HomeExtended(Home):
    @http.route()
    def web_load_menus(self, *args, **kwargs):
        """Ensure the first-level menuitem (navbar) are updated when changing
        the active company"""
        # Pass 'allowed_company_ids' to the context so the `all_group_ids` computes well
        if request.env.user.role_line_ids:
            cids_str = request.httprequest.cookies.get("cids", str(self.env.company.id))
            cids = [int(cid) for cid in cids_str.split("-")]
            request.update_context(allowed_company_ids=cids)
        response = super().web_load_menus(*args, **kwargs)

        # On logout & re-login we could see wrong menus being rendered
        # To avoid this, menu http cache must be disabled
        # Using .pop() as Werkzeug Headers no longer supports __delitem__ (del)
        response.headers.pop("Cache-Control", None)
        return response
