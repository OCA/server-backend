# Copyright 2023 Hunki Enterprises BV
# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging

import werkzeug.wrappers
from werkzeug.exceptions import Unauthorized

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ICalController(http.Controller):
    @http.route(
        "/base_ical/<int:calendar_id>",
        auth="none",
        csrf=False,
        methods=["GET"],
        type="http",
    )
    def get_ical(self, calendar_id, access_token=None):
        if not access_token:
            raise Unauthorized()

        user_id = request.env["res.users.apikeys"]._check_credentials(
            scope=f"odoo.plugin.ical.{calendar_id}",
            key=access_token,
        )
        if not user_id:
            raise Unauthorized()

        calendar = (
            http.request.env["base.ical"]
            .with_user(user_id)
            .search([("id", "=", calendar_id)])
        )
        if not calendar:
            return request.not_found()

        records = calendar._get_items()
        response = werkzeug.wrappers.Response()
        if records:
            response.last_modified = max(records.mapped("write_date"))

        response.make_conditional(request.httprequest)
        if response.status_code == 304:
            return response

        response.mimetype = "text/calendar"
        response.data = calendar._get_ical(records)
        return response
