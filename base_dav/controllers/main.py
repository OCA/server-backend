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
    @http.route(
        ["/.well-known/carddav", "/.well-known/caldav", "/.well-known/webdav"],
        type="http",
        auth="none",
        csrf=False,
    )
    def handle_well_known_request(self) -> WerkzeugResponse:
        """
        Redirect well-known CalDAV/CardDAV/WebDAV endpoints to the Radicale mount point.

        This endpoint exists for client compatibility: many CalDAV/CardDAV clients
        probe `/.well-known/caldav` or `/.well-known/carddav` and expect a redirect.

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
        """Handle WebDAV/CalDAV/CardDAV requests by proxying them to Radicale 3.x.

        The controller builds a WSGI environ from the current Odoo/Werkzeug request,
        configures Radicale to use Odoo-backed plugins (auth/storage/rights),
        executes the Radicale WSGI application, and returns an Odoo HTTP response.

        :param davpath: Path relative to the DAV mount point (``/.dav``),
            e.g. ``"admin/2/123"``; if ``None`` the root path is used.
        :type davpath: str, optional
        :param kwargs: Extra keyword arguments passed by the routing layer (unused).
        :type kwargs: Any

        :raises Exception: Any unexpected Radicale or Odoo/Werkzeug error
            during request processing will propagate as an Odoo HTTP 500.

        :return: Response produced by Radicale, including status and headers.
        :rtype: odoo.http.Response
        """
        configuration = radicale_config.load()
        configuration.update(
            {
                "auth": {"type": "odoo.addons.base_dav.radicale.auth"},
                "storage": {"type": "odoo.addons.base_dav.radicale.collection"},
                "rights": {"type": "odoo.addons.base_dav.radicale.rights"},
                "web": {"type": "none"},
                "hook": {"type": "none"},
            },
            "odoo",
        )

        app = Application(configuration)

        # Let's take WSGI environ from werkzeug/odoo
        environ = dict(request.httprequest.environ)

        # Radicale 3.x requires wsgi.errors and wsgi.input
        environ.setdefault("wsgi.errors", sys.stderr)
        method = environ.get("REQUEST_METHOD") or request.httprequest.method
        raw_body = request.httprequest.get_data(cache=False) or b""

        if method == "PROPFIND" and len(raw_body) == 0:
            raw_body = (
                b'<?xml version="1.0" encoding="utf-8"?>'
                b'<D:propfind xmlns:D="DAV:"><D:allprop/></D:propfind>'
            )

        # Force Radicale to read the body we provide
        environ["wsgi.input"] = io.BytesIO(raw_body)
        environ["CONTENT_LENGTH"] = str(len(raw_body))

        # Ensure content type is present for XML parsing
        environ.setdefault("CONTENT_TYPE", "application/xml; charset=utf-8")

        # Radicale should know that it is mounted under /.dav
        environ["SCRIPT_NAME"] = PREFIX
        environ["HTTP_X_SCRIPT_NAME"] = PREFIX

        # PATH_INFO must be absolute (with "/")
        path_info = "/" + (davpath or "")
        environ["PATH_INFO"] = path_info

        status_headers = {"status": "500 Internal Server Error", "headers": []}

        def start_response(status, headers, exc_info=None):
            """WSGI start_response callback used by Radicale.

            :param status: HTTP status line, e.g. ``"207 Multi-Status"``.
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
