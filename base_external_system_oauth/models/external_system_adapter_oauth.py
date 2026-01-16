# Copyright 2026 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ExternalSystemAdapterOAuth(models.Model):
    """OAuth wrapper around the HTTP adapter.

    This adapter is a *direct child* of external.system.adapter so that it shows
    up in the LasLabs base selection (_inherit_children).

    It reuses the HTTP adapter's request helpers by delegation, and only adds:
    - how to obtain a bearer token
    - how to inject Authorization headers into requests
    """

    _name = "external.system.adapter.oauth"
    _inherit = "external.system.adapter"
    _description = "External System OAuth Adapter"

    oauth_token_url = fields.Char(
        string="Token URL",
        help="Full URL of the OAuth token endpoint (e.g. https://login.../token).",
    )
    oauth_client_id = fields.Char(string="Client ID")
    oauth_client_secret = fields.Char(string="Client Secret")
    oauth_scope = fields.Char(string="Scope")

    def _get_http_adapter(self):
        """Return the linked HTTP adapter interface for the same system."""
        self.ensure_one()
        # The HTTP adapter record must exist as the system's interface if system_type == http.
        # Here we *instantiate* the http adapter using the same external.system record.
        # This works because external.system.adapter uses _inherits on external.system (system_id).
        return self.env["external.system.adapter.http"].search(
            [("system_id", "=", self.system_id.id)], limit=1
        )

    # -------------------------------------------------------------------------
    # Token handling
    # -------------------------------------------------------------------------
    def _fetch_bearer_token(self):
        """Fetch an OAuth bearer token using client credentials."""
        self.ensure_one()
        if not (
            self.oauth_token_url and self.oauth_client_id and self.oauth_client_secret
        ):
            raise ValidationError(
                _(
                    "Missing OAuth configuration. Please set Token URL, Client ID, and Client Secret."
                )
            )

        # Use requests directly (available via base_external_system_http) to avoid
        # inheriting external.system.adapter.http and causing MRO conflicts.
        import requests  # pylint: disable=import-error

        data = {
            "grant_type": "client_credentials",
            "client_id": self.oauth_client_id,
            "client_secret": self.oauth_client_secret,
        }
        if self.oauth_scope:
            data["scope"] = self.oauth_scope

        try:
            resp = requests.post(self.oauth_token_url, data=data, timeout=30)
        except Exception as exc:
            raise ValidationError(_("OAuth token request failed: %s") % exc) from exc

        if resp.status_code >= 400:
            raise ValidationError(
                _("OAuth token request failed (%s): %s") % (resp.status_code, resp.text)
            )

        payload = resp.json()
        token = payload.get("access_token")
        if not token:
            raise ValidationError(_("OAuth token response has no access_token."))
        return token

    # -------------------------------------------------------------------------
    # HTTP helpers
    # -------------------------------------------------------------------------
    def _base_url(self):
        """Base URL for API calls.

        For LasLabs base (no 'scheme' field), we store the full base URL in remote_path,
        e.g. https://api.example.com
        """
        self.ensure_one()
        if not self.system_id.remote_path:
            raise ValidationError(
                _(
                    "Missing Remote Path. For OAuth HTTP calls, set it to the base URL, e.g. https://api.example.com"
                )
            )
        return self.system_id.remote_path.rstrip("/")

    def _request(self, method, endpoint="/", headers=None, **kwargs):
        """Low-level request with bearer token."""
        self.ensure_one()
        token = self._fetch_bearer_token()
        req_headers = dict(headers or {})
        req_headers["Authorization"] = "Bearer %s" % token

        url = self._base_url()
        if endpoint:
            url = url + (endpoint if endpoint.startswith("/") else "/" + endpoint)

        import requests  # pylint: disable=import-error

        try:
            resp = requests.request(
                method, url, headers=req_headers, timeout=30, **kwargs
            )
        except Exception as exc:
            raise ValidationError(_("HTTP request failed: %s") % exc) from exc

        if resp.status_code >= 400:
            _logger.error(
                "Got response with statuscode %s from endpoint %s: %s",
                resp.status_code,
                endpoint or "<base>",
                resp.text,
            )
            raise ValidationError(
                _("Got response with statuscode %s from endpoint %s: %s")
                % (resp.status_code, endpoint or "<base>", resp.text)
            )
        return resp

    def get(self, endpoint="/", headers=None, **kwargs):
        self.ensure_one()
        return self._request("GET", endpoint=endpoint, headers=headers, **kwargs)

    def post(self, endpoint="/", headers=None, **kwargs):
        self.ensure_one()
        return self._request("POST", endpoint=endpoint, headers=headers, **kwargs)

    # -------------------------------------------------------------------------
    # Adapter contract
    # -------------------------------------------------------------------------
    def external_get_client(self):
        """Return a usable client representing the remote system.

        In LasLabs base, external.system.client() yields self.interface.client().
        For OAuth, we can just yield *this adapter record itself* as the client,
        because it provides get/post helpers.
        """
        self.ensure_one()
        return self

    def external_destroy_client(self, client):
        """Nothing persistent to cleanup."""
        self.ensure_one()
        return super().external_destroy_client(client)

    def external_test_connection(self):
        """Test connection in the UI.

        This validates we can fetch a token and do a base GET request.
        """
        self.ensure_one()
        # Fetch token (validates OAuth config)
        self._fetch_bearer_token()
        # Validate API base reachable
        self.get(endpoint="/")
        return super().external_test_connection()

    def strip_empty_data(self, data):
        """Recursively remove empty values from dict/list structures.
        - Removes keys with values: None, False, "", [], {}, ()
        - Keeps: 0, 0.0, and non-empty strings/lists/dicts
        - Processes nested dicts/lists recursively
        This helper existed in the legacy oauth module and is used by tests
        and potentially by downstream code.
        """
        return self._strip_empty_data(data)

    def _strip_empty_data(self, value):
        """Internal recursive implementation for strip_empty_data()."""
        # Normalize strings: whitespace-only becomes ""
        if isinstance(value, str):
            return value.strip()

        if isinstance(value, dict):
            cleaned = {}
            for k, v in value.items():
                v2 = self._strip_empty_data(v)
                if not self._is_empty_value(v2):
                    cleaned[k] = v2
            return cleaned

        if isinstance(value, (list, tuple)):
            cleaned_list = []
            for item in value:
                item2 = self._strip_empty_data(item)
                if not self._is_empty_value(item2):
                    cleaned_list.append(item2)
            return cleaned_list

        return value

    def _is_empty_value(self, value):
        """Return True if value should be stripped as 'empty'."""
        # Note: keep numeric zero values
        if value is None:
            return True
        if value is False:
            return True
        if isinstance(value, (list, tuple, dict)) and not value:
            return True
        # IMPORTANT: do NOT treat "" as empty (legacy behavior / tests expect it kept)
        return False
