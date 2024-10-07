# Copyright 2024 Therp BV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=no-member
"""Extend external system with ms client assertion authentication."""
import json
import logging
import os

import msal

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

global_token_cache = msal.TokenCache()


class ExternalSystemAdapterMsClientAssertion(models.AbstractModel):
    """OAuth for Microsoft Client Assertion."""

    # Because of slots this class can not be inherited.
    __slots__ = ["global_app"]

    _name = "external.system.adapter.ms.client.assertion"
    _inherit = [
        "external.system.adapter.http",
        "external.system.interaction.oauth.mixin",
    ]
    _description = __doc__

    def external_get_client(self):
        """Return token that can be used to access remote system."""
        client = super().external_get_client()
        self.global_app = self._get_global_app()
        self._get_token()  # Do this immediately to be sure of connection.
        return client

    def _get_global_app(self):
        """Initialize long lived global app here for performance reasons."""
        server = self.system_id
        oauth = server.oauth_definition_id
        authority = "%(auth_endpoint)s/%(tenant_id)s" % {
            "auth_endpoint": oauth.auth_endpoint,
            "tenant_id": oauth.tenant_id,
        }
        global_app = msal.ConfidentialClientApplication(
            oauth.client_id,
            authority=authority,
            client_credential={
                "thumbprint": server.private_key_thumbprint,
                "private_key": self._get_private_key(server.private_key),
                "passphrase": server.private_key_password,
            },
            # Let this app (re)use an existing token cache.
            # If absent, ClientApplication will create its own empty token cache
            token_cache=global_token_cache,
        )
        return global_app

    def _get_private_key(self, private_key):
        """Get private key from file system, or use it directly."""
        use_direct = private_key.startswith("-----BEGIN ENCRYPTED PRIVATE KEY-----")
        if use_direct:
            return private_key
        attachment_model = self.env["ir.attachment"]
        full_path = os.path.join(attachment_model._filestore(), "keystore", private_key)
        with open(full_path) as file:
            private_key = file.read()
        return private_key

    def _get_token(self):
        """Return token by generating it on the fly using the msal application."""
        return self._get_access_token_microsoft_client_assertion()

    def _get_access_token_microsoft_client_assertion(self):
        """Get access token from Microsoft Client Assertion."""
        oauth = self.system_id.oauth_definition_id
        # Since MSAL 1.23, acquire_token_for_client(...) will automatically look up
        # a token from cache, and fall back to acquire a fresh token when needed.
        scopes = [oauth.scope % oauth.client_id]  # scopes is an array of url's.
        global_app = self.global_app
        response = global_app.acquire_token_for_client(scopes=scopes)
        if "access_token" not in response:
            raise UserError(_("Oauth response did not contain access_token"))
        _logger.debug("Token was obtained from: %s", response["token_source"])
        return response["access_token"]

    def _set_headers(self, headers):
        """Set headers in keyword arguments."""
        result = super()._set_headers(headers)
        # Add x5t header
        server = self.system_id
        x5t = {
            "alg": "RS256",
            "typ": "JWT",
            "x5t": server.private_key_thumbprint,
        }
        headers["x5t"] = json.dumps(x5t)
        return result
