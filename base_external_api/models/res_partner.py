# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _render_api_demo(self):
        tmpl = self.env["apicli.document"].get_document(code="DemoCustomerMaster")
        return tmpl.render(self)

    def action_api_demo(self):
        res = self._render_api_demo()
        for k, v in res.items():
            _logger.info("=> %s:\n%s", k, v)
