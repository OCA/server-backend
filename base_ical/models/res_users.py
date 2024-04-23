# Copyright 2023 Hunki Enterprises BV
# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    ical_ids = fields.One2many("base.ical", compute="_compute_ical_ids")

    def _compute_ical_ids(self):
        domain = [("allowed_users_ids", "=", self.env.uid)]
        self.write({"ical_ids": self.env["base.ical"].search(domain)})

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["ical_ids"]

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        calendars = self.env["base.ical"].search([("auto", "=", True)])
        calendars.sudo().write({"allowed_users_ids": [(4, result.id)]})
        return result
