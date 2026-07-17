# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""HTTP(S) adapter for :class:`external.system`."""

import logging

import requests
from requests import exceptions as req_exc

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ExternalSystemAdapterHTTP(models.Model):
    """HTTP external system adapter."""

    _name = "external.system.adapter.http"
    _inherit = "external.system.adapter"
    _description = "External System HTTP"

    def external_get_client(self):
        self.ensure_one()
        return self

    def external_destroy_client(self, client):
        self.ensure_one()
        return super().external_destroy_client(client)

    def external_test_connection(self):
        """Test connection in the UI by doing a GET on the base URL."""
        self.ensure_one()
        try:
            self.get(endpoint=None)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(_("Connection failed.\n\nDETAIL: %s") % exc) from exc
        return super().external_test_connection()

    def get(self, endpoint=None, params=None, timeout=16, **kwargs):
        """GET helper."""
        self.ensure_one()
        url = self._get_url(endpoint=endpoint)
        _logger.debug("Will GET %s", url)
        try:
            response = requests.get(url, params=params, timeout=timeout, **kwargs)
        except req_exc.RequestException as exc:
            _logger.error("GET %s failed: %s", url, exc)
            raise ValidationError(
                _("GET request failed for %(url)s.\n\nDETAIL: %(detail)s")
                % {"url": url, "detail": exc}
            ) from exc
        return self._return_checked_response(endpoint, response)

    def post(self, endpoint=None, data=None, json=None, timeout=16, **kwargs):
        """POST helper."""
        self.ensure_one()
        url = self._get_url(endpoint=endpoint)
        _logger.debug("Will POST %s", url)
        try:
            response = requests.post(
                url, data=data, json=json, timeout=timeout, **kwargs
            )
        except req_exc.RequestException as exc:
            _logger.error("POST %s failed: %s", url, exc)
            raise ValidationError(
                _("POST request failed for %(url)s.\n\nDETAIL: %(detail)s")
                % {"url": url, "detail": exc}
            ) from exc
        return self._return_checked_response(endpoint, response)

    def put(self, endpoint=None, data=None, json=None, timeout=16, **kwargs):
        """PUT helper."""
        self.ensure_one()
        url = self._get_url(endpoint=endpoint)
        _logger.debug("Will PUT %s", url)
        try:
            response = requests.put(
                url, data=data, json=json, timeout=timeout, **kwargs
            )
        except req_exc.RequestException as exc:
            _logger.error("PUT %s failed: %s", url, exc)
            raise ValidationError(
                _("PUT request failed for %(url)s.\n\nDETAIL: %(detail)s")
                % {"url": url, "detail": exc}
            ) from exc
        return self._return_checked_response(endpoint, response)

    def delete(self, endpoint=None, params=None, timeout=16, **kwargs):
        """DELETE helper."""
        self.ensure_one()
        url = self._get_url(endpoint=endpoint)
        _logger.debug("Will DELETE %s", url)
        try:
            response = requests.delete(url, params=params, timeout=timeout, **kwargs)
        except req_exc.RequestException as exc:
            _logger.error("DELETE %s failed: %s", url, exc)
            raise ValidationError(
                _("DELETE request failed for %(url)s.\n\nDETAIL: %(detail)s")
                % {"url": url, "detail": exc}
            ) from exc
        return self._return_checked_response(endpoint, response)

    def _get_url(self, endpoint=None, url_suffix=None):
        """Build full URL for an endpoint"""
        self.ensure_one()
        system = self.system_id
        endpoint_record = None
        if endpoint:
            endpoint_record = self.env["external.system.endpoint"].search(
                [("system_id", "=", system.id), ("name", "=", endpoint)],
                limit=1,
            )
            if not endpoint_record:
                raise UserError(
                    _("Endpoint %(endpoint)s not found on system %(system_name)s")
                    % {"endpoint": endpoint, "system_name": system.name}
                )
        host = (system.host or "").strip()
        if host.startswith(("http://", "https://")):
            base = host.rstrip("/")
        else:
            base = ("https://" + host).rstrip("/")
        port = ":" + str(system.port) if system.port else ""
        remote_path = (system.remote_path or "").rstrip("/")
        endpoint_path = endpoint_record.endpoint if endpoint_record else ""
        suffix = url_suffix or ""
        return f"{base}{port}{remote_path}{endpoint_path}{suffix}"

    def _return_checked_response(self, endpoint, response):
        """Validate response."""
        if response.status_code >= 400:
            text = response.text or ""
            _logger.error(
                "Got response with statuscode %(status)s from endpoint %(endpoint)s: %(text)s",
                {
                    "status": str(response.status_code),
                    "endpoint": endpoint or "<base>",
                    "text": text,
                },
            )
            raise ValidationError(
                _(
                    "Communication failure with %(endpoint)s "
                    "(HTTP %(status)s).\n\nDETAIL: %(detail)s"
                )
                % {
                    "endpoint": endpoint or "<base>",
                    "status": response.status_code,
                    "detail": (text or "").strip(),
                }
            )

        _logger.info("Succesfull communication with endpoint %s", endpoint or "<base>")
        return response
