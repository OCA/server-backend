# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import logging
import pprint
import urllib.parse

import requests
import xmltodict

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class ApicliConnection(models.Model):
    _name = "apicli.connection"
    _description = "API Client Connection"

    @api.depends(
        "authentication_type",
        "connection_type",
        "code",
        "user",
        "password",
        "api_clientid",
        "api_secret",
        "active",
    )
    def _compute_state(self):
        "Onchange of the dependecy fields, set state to unconfirmed"
        for conn in self:
            conn.state = "unconfirmed"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char(
        help="Identifier that custom code can use to lookup this connection"
    )
    address = fields.Char(required=True)
    connection_type = fields.Selection(
        [("http", "HTTP(S)")], default="http", required=True
    )
    authentication_type = fields.Selection(
        [
            ("user_password", "User and Password"),
            ("api_secret", "API Client and Secret"),
            ("api_key", "API Key"),
            ("api", "API Key (Deprecated)"),  # TODO: remove
        ],
        default="user_password",
        required=True,
    )
    user = fields.Char()
    password = fields.Char()
    api_clientid = fields.Char(string="API Client ID")
    api_key = fields.Char(string="API Key")
    api_secret = fields.Char(string="API Secret")
    headers_add = fields.Text()
    state = fields.Selection(
        selection=[("unconfirmed", "Unconfirmed"), ("confirmed", "Confirmed")],
        default="unconfirmed",
        compute="_compute_state",
        copy=False,
        readonly=False,
        required=True,
        store=True,
    )
    test_button_endpoint = fields.Char()

    test_endpoint = fields.Char()
    test_verb = fields.Char(default="GET")
    test_headers_add = fields.Text()
    test_payload = fields.Text()
    test_response = fields.Text()
    test_response_status = fields.Text()

    def _build_url(self, path):
        """
        Build the URL address to send the message to
        """
        if self.connection_type == "http":
            return urllib.parse.urljoin(self.address, path)

    def _build_params(self, params_add):
        """
        Build the URL parameter options
        """
        if self.connection_type == "http":
            params = {}
            if params_add:
                params.update(params_add)
            return params

    def _build_headers(self, headers_add=None, token=None):
        """
        Build the message Request Header
        """
        if self.connection_type == "http":
            headers = json.loads(self.headers_add or "{}")
            if self.authentication_type == "api_key":
                headers["apikey"] = self.api_key
            if token:
                headers["Authorization"] = "Bearer " + token
            if headers_add:
                headers.update(headers_add)
            return headers

    def api_check_error(self, response, suppress_errors=False):
        """
        Parse the response for errors and prepare a user friendly message
        """
        if self.connection_type == "http":
            msg = None
            if response.status_code not in [200, 201, 204]:
                msg = _("Error running API request:\n%(code)s %(reason)s\n%(text)s") % {
                    "code": str(response.status_code),
                    "reason": str(response.reason),
                    "text": str(response.text),
                }
                if not suppress_errors:
                    raise exceptions.ValidationError(msg)
            return msg

    @api.model
    def get_by_code(self, code=None, error_when_not_found=True):
        """
        Get the connection Object matching an identifier Code
        """
        domain = []
        if code:
            domain = [("code", "=like", code)]
        res = self.search(domain)
        if len(res) != 1 and error_when_not_found:
            raise exceptions.UserError(
                _("Found %(count)d results when looking for connection %(code)s")
                % {
                    "count": len(res),
                    "code": code,
                }
            )
        return res

    def api_get_token(self):
        # TODO: Implement a sane Basic Auth default
        token = None
        return token

    def api_call_after(self, response, **kwargs):
        """
        Hook to run logic after the API raw call is made
        """
        return

    def api_call_raw(
        self,
        endpoint,
        verb="GET",
        headers_add=None,
        params=None,
        payload=None,
        suppress_errors=None,
        token=None,
        **kwargs,
    ):
        """
        Core logic to send an API message.
        Returns a Response object (for HTTP requests).
        Extend to add other connection types.
        """
        if self.connection_type == "http":
            request_url = self._build_url(endpoint)
            if not token:
                token = self.api_get_token()
            request_headers = self._build_headers(headers_add, token)
            request_params = self._build_params(params)
            request_data = payload if type(payload) is str else json.dumps(payload)
            _logger.debug(
                "\nRequest for %s %s:\n%s",
                request_url,
                verb,
                payload if type(payload) is str else pprint.pformat(payload, indent=1),
            )
            response = requests.request(
                verb,
                request_url,
                params=request_params,
                data=request_data or "",
                headers=request_headers,
            )
            _logger.debug(
                "\nResponse %s: %s",
                response.status_code,
                pprint.pformat(response.json(), indent=1)
                if response.text.startswith("{")
                else response.text,
            )
            self.api_call_after(response, **kwargs)
            if not suppress_errors:
                self.api_check_error(response)
            return response

    @api.model
    def response_to_dict(self, response):
        data_dict = {}
        try:
            if type(response) is dict:
                data_dict = response
            else:
                data_dict = response.json()
        except Exception:
            try:
                data_dict = xmltodict.parse(response.text)
            except Exception:
                data_dict = {"message": response.text}
        return data_dict

    def api_call(
        self,
        endpoint,
        verb="GET",
        headers_add=None,
        params=None,
        payload=None,
        suppress_errors=None,
        token=None,
        store_message=True,
        **kwargs,
    ):
        """
        Same as api_call_raw(), but returns a dict
        with the response data
        """
        response = self.api_call_raw(
            endpoint,
            verb,
            headers_add,
            params,
            payload,
            suppress_errors,
            token,
            **kwargs,
        )
        res = self.response_to_dict(response)
        if store_message:
            self.env["apicli.message"].create(
                {
                    "connection_id": self.id,
                    "endpoint": endpoint,
                    "content": payload,
                    "state": "done",
                    "direction": "out",
                }
            )
        return res

    def _api_test_call(self):
        """
        Extend to implement connection test call
        """
        if self.connection_type == "http":
            self.api_call(self.test_button_endpoint)
            return True
        return False

    def api_test(self):
        """
        Do not extend this method.
        Instead extend _api_test_call() to implement the conenction specific tests
        """
        if not self._api_test_call():
            raise exceptions.UserError(_("Connection test not succesfull"))
        self.state = "confirmed"

    def action_test_api_call(self):
        response = self.api_call_raw(
            self.test_endpoint,
            self.test_verb or "GET",
            self.test_headers_add,
            payload=self.test_payload,
        )
        self.test_response_status = response.status_code
        self.test_response = pprint.pformat(response.json(), indent=1)
