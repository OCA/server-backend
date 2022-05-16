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

    def render_partner_master(self):
        tmpl = self.env["apicli.document"].get_document(code="PartnerMaster")
        res = tmpl.render(self)
        _logger.info(res)
        return res

    def action_upload_partner_master(self):
        conn = self.env["apicli.connection"].get_by_code("DemoFTP")
        partner_master_dict = self.render_partner_master()
        for name, payload in partner_master_dict.items():
            conn.api_call(name, payload=payload)

    def action_download_partner_master(self):
        conn = self.env["apicli.connection"].get_by_code("DemoFTP")
        conn.cron_download_ftp_files(subdirectory="~/Inbox")
