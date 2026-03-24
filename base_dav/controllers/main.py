# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import io
import sys

import werkzeug
from radicale import config as radicale_config
from radicale.app import Application
from werkzeug.wrappers.response import Response as WerkzeugResponse

from odoo import http
from odoo.http import request

PREFIX = "/.dav"


class Main(http.Controller):
    def _get_radicale_config(self):
        """Return Radicale plugin configuration for DAV requests."""
        return {
            "auth": {"type": "odoo.addons.base_dav.radicale.auth"},
            "storage": {"type": "odoo.addons.base_dav.radicale.collection"},
            "rights": {"type": "odoo.addons.base_dav.radicale.rights"},
            "web": {"type": "none"},
        }

    @http.route(
        ["/.well-known/carddav", "/.well-known/caldav", "/.well-known/webdav"],
        type="http",
        auth="none",
        csrf=False,
    )
    def handle_well_known_request(self) -> WerkzeugResponse:
        """
        Redirect well-known CalDAV/CardDAV/WebDAV endpoints to the Radicale mount point.

        :return: HTTP 301 redirect response to ``/.dav``.
        :rtype: werkzeug.wrappers.response.Response
        """
        return werkzeug.utils.redirect(PREFIX, 301)

    @http.route(
        [PREFIX, f"{PREFIX}/<path:davpath>"],
        type="http",
        auth="none",
        csrf=False,
    )
    def handle_dav_request(self, davpath=None, **kwargs):
        """Proxy WebDAV/CalDAV/CardDAV requests to the Radicale app.

        :param davpath: Path relative to the DAV mount point.
        :type davpath: str | None
        :param kwargs: Extra route keyword arguments, unused.
        :type kwargs: dict

        :return: Response produced by Radicale.
        :rtype: odoo.http.Response
        """
        configuration = radicale_config.load()
        configuration.update(self._get_radicale_config(), "odoo")
        app = Application(configuration)

        environ = dict(request.httprequest.environ)
        environ.setdefault("wsgi.errors", sys.stderr)

        raw_body = request.httprequest.get_data(cache=False) or b""
        environ["wsgi.input"] = io.BytesIO(raw_body)
        environ["CONTENT_LENGTH"] = str(len(raw_body))

        environ.setdefault("CONTENT_TYPE", "application/xml; charset=utf-8")
        environ["SCRIPT_NAME"] = PREFIX
        environ["HTTP_X_SCRIPT_NAME"] = PREFIX
        environ["PATH_INFO"] = "/" + (davpath or "")

        status_headers = {"status": "500 Internal Server Error", "headers": []}

        def start_response(status, headers, exc_info=None):
            """WSGI start_response callback used by Radicale.

            :param status: HTTP status line.
            :type status: str
            :param headers: Sequence of ``(header_name, header_value)``.
            :type headers: Sequence[tuple[str, str]]
            :param exc_info: Optional exception info as per WSGI spec (unused).
            :type exc_info: Any, optional
            """
            status_headers["status"] = status
            status_headers["headers"] = headers

        result_iter = app(environ, start_response)
        try:
            response_body = b"".join(result_iter) if result_iter else b""
        finally:
            if hasattr(result_iter, "close"):
                result_iter.close()

        headers = status_headers["headers"]
        if isinstance(headers, dict):
            headers = list(headers.items())

        return http.Response(
            response=response_body,
            status=status_headers["status"],
            headers=headers,
        )
