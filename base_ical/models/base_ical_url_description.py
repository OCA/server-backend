# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from urllib.parse import urlparse, urlunparse

from odoo import _, fields, models
from odoo.exceptions import AccessError

from odoo.addons.base.models.res_users import check_identity


class BaseIcalUrlDescription(models.TransientModel):
    _name = "base.ical.url.description"
    _description = "Description for iCalendar"

    calendar_id = fields.Many2one("base.ical", required=True)
    name = fields.Char("Description", required=True)

    def _make_url(self):
        if not self.user_has_groups("base.group_user"):
            raise AccessError(_("Only internal users can create API keys"))

        scope = f"odoo.plugin.ical.{self.calendar_id.id}"

        token = self.env["res.users.apikeys"]._generate(scope, f"Calendar: {self.name}")

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return urlunparse(
            urlparse(base_url)._replace(
                path=f"/base_ical/{self.calendar_id.id}",
                query=f"access_token={token}",
            )
        )

    @check_identity
    def make_url(self):
        url = self._make_url()
        return {
            "type": "ir.actions.act_window",
            "res_model": "base.ical.url.show",
            "name": "iCalendar URL",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_url": url,
            },
        }
