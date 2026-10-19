# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import werkzeug

from odoo import http

PREFIX = "/.dav"


class Main(http.Controller):
    # Only the plain WebDAV service is advertised here, for the scanner upload
    # flow; the /.dav endpoint itself is served by the bureaucracy module.
    #
    # CalDAV and CardDAV discovery used to be advertised from here too, but the
    # route below was disabled in commit 8a9983f: the Radicale 3.x bootstrap it
    # wrapped is incompatible with the installed Radicale (radicale.config.
    # INITIAL_CONFIG no longer exists, radicale.rights lost AuthenticatedRights /
    # OwnerOnlyRights / OwnerWriteRights, and the storage plugin base classes
    # moved). Rather than port that plugin layer, the dav_server module in this
    # same repository implements CalDAV and CardDAV directly against Odoo's
    # models and owns /.well-known/caldav and /.well-known/carddav.
    #
    # Two modules answering the same path would be a silent first-match-wins
    # routing conflict, so this list is deliberately narrowed to /webdav.
    @http.route(
        "/.well-known/webdav",
        type="http",
        auth="none",
        csrf=False,
        methods=["GET", "PROPFIND", "REPORT", "PUT", "DELETE", "OPTIONS"],
    )
    def handle_well_known_request(self):
        return werkzeug.utils.redirect(PREFIX, 301)
