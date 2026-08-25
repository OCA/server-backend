# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from configparser import RawConfigParser as ConfigParser

import werkzeug

from odoo import http
from odoo.http import request

try:
    import radicale
except ImportError:
    radicale = None

PREFIX = "/.dav"


class Main(http.Controller):
    @http.route(
        ["/.well-known/carddav", "/.well-known/caldav", "/.well-known/webdav"],
        type="http",
        auth="none",
        csrf=False,
        methods=["GET", "PROPFIND", "REPORT", "PUT", "DELETE", "OPTIONS"],
    )
    def handle_well_known_request(self):
        return werkzeug.utils.redirect(PREFIX, 301)

    # NOTE: the `/.dav` route itself is intentionally NOT registered here.
    # Calendar/addressbook support via Radicale is broken on Radicale 3.x
    # (the original bootstrap code references INITIAL_CONFIG, which no longer
    # exists), and the only production use case is scanner file uploads.
    # Bureaucracy registers its own `/.dav` controller (webdav_files_controller)
    # that handles dav_type == 'files' collections. If you need CalDAV/CardDAV,
    # restore the @http.route decorator below and fix the Radicale bootstrap.
        if radicale is None:
            return http.Response(
                "Radicale is not installed. "
                "Please install it with: pip install radicale",
                status=500,
            )

        config = ConfigParser()
        for section, values in radicale.config.INITIAL_CONFIG.items():
            config.add_section(section)
            for key, data in values.items():
                config.set(section, key, data["value"])
        config.set("auth", "type", "odoo.addons.base_dav.radicale.auth")
        config.set("storage", "type", "odoo.addons.base_dav.radicale.collection")
        config.set("rights", "type", "odoo.addons.base_dav.radicale.rights")
        config.set("web", "type", "none")
        application = radicale.Application(
            config,
            logging.getLogger("radicale"),
        )

        response = None

        def start_response(status, headers):
            nonlocal response
            response = http.Response(status=status, headers=headers)

        result = application(
            dict(
                request.httprequest.environ,
                HTTP_X_SCRIPT_NAME=PREFIX,
                PATH_INFO=davpath or "",
            ),
            start_response,
        )
        response.stream.write(result and result[0] or b"")
        return response
