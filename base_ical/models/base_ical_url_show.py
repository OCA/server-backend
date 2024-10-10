# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class BaseIcalUrlShow(models.AbstractModel):
    _name = "base.ical.url.show"
    _description = "Show URL for iCalendar"

    id = fields.Id()
    url = fields.Char(readonly=True)
