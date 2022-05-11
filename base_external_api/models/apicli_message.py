# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import re

import xmltodict

from odoo import api, fields, models


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

    def _parse_content(self):
        data = {}
        first_char = (self.content or "").lstrip()[:1]
        if first_char == "<":
            # XML data convert to dict
            data = xmltodict.parse(self.content)
        elif first_char == "{":
            # JSON data convert to dict
            data = json.loads(self.content)
        return data

    def process_messages(self):
        hooks = self.env["apicli.hook"].search(
            [("method_name", "!=", False), ("model_id", "!=", False)]
        )
        for message in self.filtered(lambda x: x.state == "todo"):
            selected_hook = hooks.filtered(
                lambda x: re.search(x.match_regexp, message.endpoint, re.I)
            )[:1]
            if selected_hook:
                process_model = self.env[selected_hook.model_id.model]
                process_method = getattr(process_model, selected_hook.method_name)
                if process_method:
                    datas = {
                        "endpoint": message.endpoint,
                        "raw": message.content,
                        "parsed": message._parse_content(),
                    }
                    # FIXME: add try/exception and handle success or error
                    process_method(datas)

    @api.model
    def scan_queue_process(self):
        messages = self.search([("state", "=", "todo")])
        messages.process_messages()