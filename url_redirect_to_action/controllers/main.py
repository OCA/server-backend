from odoo import http
from odoo.http import request


class UrlRedirectToAction(http.Controller):
    @http.route("/web/redirect/<string:action_name>", type="http", auth="user")
    def redirect(self, action_name, **kwargs):
        env = request.env
        env["base"]._redirect_to_action_from_url(action_name, kwargs)
        known_action = env.ref(action_name, raise_if_not_found=False)
        if known_action:
            path = known_action.path
            if path:
                return request.redirect(f"/odoo/{path}")
            else:
                return request.redirect(f"/odoo/action-{known_action.id}")
