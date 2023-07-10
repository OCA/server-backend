# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import http


class MyController(http.Controller):
    @http.route(
        "/base_ical/<string:token>",
        auth="public",
        csrf=False,
        methods=["GET"],
        type="http",
    )
    def get_ical(self, token):
        # TODO: respect if-modified-since headers
        token = (
            http.request.env["base.ical.token"].sudo().search([("token", "=", token)])
        )
        if not token:
            return http.request.not_found()
        response = http.request.make_response(
            token.ical_id.with_user(token.user_id)._get_ical(),
            headers={"content-type": "text/calendar"},
        )
        return response
