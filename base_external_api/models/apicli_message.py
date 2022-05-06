# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ApicliMessage(models.Model):
    _name = "apicli.message"
    _description = "API Client message"
    _rec_name = "endpoint"

    connection_id = fields.Many2one("apicli.connection")
    endpoint = fields.Char()
    content = fields.Text()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("todo", "TODO"),
            ("done", "Done"),
            ("error", "Error"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
    )
