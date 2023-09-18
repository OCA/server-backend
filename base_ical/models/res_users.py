# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    ical_ids = fields.One2many("base.ical", compute="_compute_ical_ids")

    def _compute_ical_ids(self):
        for this in self:
            this.ical_ids = self.env["base.ical"].search([])

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["ical_ids"]
