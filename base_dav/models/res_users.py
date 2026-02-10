# Copyright 2026
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import secrets

from odoo import api, fields, models

from ..controllers.main import PREFIX


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _generate_carddav_token(self):
        return secrets.token_urlsafe(24)

    carddav_url = fields.Char(
        compute="_compute_carddav_url",
        string="CardDAV URL",
    )
    carddav_token = fields.Char(
        string="CardDAV Token",
        help="Password used for CardDAV Digest authentication.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._ensure_carddav_token()
        return users

    def write(self, vals):
        result = super().write(vals)
        if "carddav_token" not in vals:
            self._ensure_carddav_token()
        return result

    @api.depends("login")
    def _compute_carddav_url(self):
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url")
        )
        collection = self.env["dav.collection"]._ensure_default_addressbook()

        for user in self:
            if base_url and collection and user.login:
                user.carddav_url = (
                    f"{base_url}{PREFIX}/{user.login}/{collection.id}"
                )
            else:
                user.carddav_url = False

    def _ensure_carddav_token(self):
        for user in self.filtered(lambda u: not u.carddav_token):
            user.carddav_token = self._generate_carddav_token()

    def action_generate_carddav_token(self):
        for user in self:
            user.carddav_token = self._generate_carddav_token()
        return True
