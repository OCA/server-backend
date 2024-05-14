# Copyright 2023-2024 Therp BV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Extend external system with oauth authentication."""

from odoo import models


class ExternalSystemAdapterOAuth(models.AbstractModel):
    """This is an Interface implementing the OAuth module."""

    __slots__ = ["token"]

    _name = "external.system.adapter.oauth"
    _inherit = [
        "external.system.adapter.http",
        "external.system.interaction.oauth.mixin",
    ]
    _description = __doc__

    def external_get_client(self):
        """Return token that can be used to access remote system."""
        client = super().external_get_client()
        oauth = self.system_id.oauth_definition_id
        self.token = oauth.get_access_token()
        return client

    def external_destroy_client(self, client):
        """Perform any logic necessary to destroy the client connection."""
        if self.token:
            self.token = None

    def post(self, endpoint=None, data=None, json=None, **kwargs):
        """Send post request."""
        headers = kwargs.pop("headers", {})
        self._set_headers(headers)
        return super().post(
            endpoint=endpoint, data=data, json=json, headers=headers, **kwargs
        )

    def _get_token(self):
        """Trivial implementation."""
        return self.token
