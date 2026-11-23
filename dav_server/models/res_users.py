# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Self-service DAV connection details on the user's own Preferences form."""

from urllib.parse import quote

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ResUsers(models.Model):
    _inherit = "res.users"

    dav_server_url = fields.Char(compute="_compute_dav_setup", string="DAV server URL")
    dav_username = fields.Char(compute="_compute_dav_setup", string="Username")
    dav_caldav_url = fields.Char(compute="_compute_dav_setup", string="CalDAV URL")
    dav_carddav_url = fields.Char(compute="_compute_dav_setup", string="CardDAV URL")
    dav_collections_info = fields.Text(
        compute="_compute_dav_setup", string="Available collections"
    )

    @api.depends("login")
    def _compute_dav_setup(self):
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", "")
            .rstrip("/")
        )
        for user in self:
            login = quote(user.login or "", safe="")
            user.dav_server_url = f"{base_url}/dav/" if base_url else ""
            user.dav_username = user.login or ""
            user.dav_caldav_url = f"{base_url}/dav/caldav/{login}/" if base_url else ""
            user.dav_carddav_url = f"{base_url}/dav/carddav/{login}/" if base_url else ""
            user.dav_collections_info = user._dav_collection_names()

    def _dav_collection_names(self):
        """Names of calendar/address-book collections exposing records to this user."""
        names = []
        # dav.collection has no read ACL for regular users: list it as sudo,
        # but resolve each domain under the user's own rights.
        collections = self.env["dav.collection"].sudo().search(
            [("dav_type", "in", ("calendar", "addressbook"))]
        )
        for collection in collections:
            try:
                domain = safe_eval(collection.domain or "[]", {"user": user})
                model = self.env[collection.model_id.model].with_user(user)
                if model.search_count(domain, limit=1):
                    names.append(f"{collection.name} ({collection.dav_type})")
            except Exception:
                # A collection the user cannot resolve is not advertised.
                continue
        return "\n".join(sorted(names))
