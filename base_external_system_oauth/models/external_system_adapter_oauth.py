# Copyright 2023-2024 Therp BV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Extend external system with oauth authentication."""

from odoo import models


class ExternalSystemAdapterOAuth(models.AbstractModel):
    """This is an Interface implementing the OAuth module."""

    _name = "external.system.adapter.oauth"
    _inherit = [
        "external.system.adapter.http",
        "external.system.interaction.oauth.mixin",
    ]
    _description = __doc__

    def get_token(self):
        """Get token from adapter_memory."""
        return self.env.context["adapter_memory"].get("token", None)

    def set_token(self, value):
        """Store token in adapter_memor."""
        self.env.context["adapter_memory"]["token"] = value

    def del_token(self):
        """Get system from environment."""
        if "token" in self.env.context["adapter_memory"]:
            del self.env.context["adapter_memory"]["token"]

    token = property(get_token, set_token, del_token)

    def external_get_client(self):
        """Return token that can be used to access remote system."""
        client = super().external_get_client()
        oauth = self.system_id.oauth_definition_id
        self.token = oauth.get_access_token()
        return client

    def external_destroy_client(self, client):
        """Delete token from client."""
        del self.token
        return super().external_destroy_client(client)

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
