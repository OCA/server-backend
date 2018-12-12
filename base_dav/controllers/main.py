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

PREFIX = '/.dav'


class Main(http.Controller):
    @http.route(
        ['/.well-known/carddav', '/.well-known/caldav', '/.well-known/webdav'],
        type='http', auth='none', csrf=False,
    )
    def handle_well_known_request(self):
        return werkzeug.utils.redirect(PREFIX, 301)

    @http.route(
        [PREFIX, '%s/<path:davpath>' % PREFIX], type='http', auth='none',
        csrf=False,
    )
    def handle_dav_request(self, davpath=None):
        config = ConfigParser()
        for section, values in radicale.config.INITIAL_CONFIG.items():
            config.add_section(section)
            for key, data in values.items():
                config.set(section, key, data["value"])
        config.set('auth', 'type', 'odoo.addons.base_dav.radicale.auth')
        config.set(
            'storage', 'type', 'odoo.addons.base_dav.radicale.collection'
        )
        config.set(
            'rights', 'type', 'odoo.addons.base_dav.radicale.rights'
        )
        config.set('web', 'type', 'none')
        application = radicale.Application(
            config, logging.getLogger('radicale'),
        )

        response = None

        def start_response(status, headers):
            nonlocal response
            response = http.Response(status=status, headers=headers)

        result = application(
            dict(
                request.httprequest.environ,
                HTTP_X_SCRIPT_NAME=PREFIX,
                PATH_INFO=davpath or '',
            ),
            start_response,
        )
        response.stream.write(result and result[0] or b'')
        return response
