# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import re

import xmltodict

from odoo import api, fields, models, registry


class ApicliMessage(models.Model):
    _name = "apicli.message"
    _description = "API Client message"
    _rec_name = "endpoint"
    _order = "id desc"

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
    result = fields.Text(readonly=True)
    processed_hook_id = fields.Many2one("apicli.hook")

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

    def process_messages(self, stop_on_error=False):

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
                    if stop_on_error:
                        result = process_method(datas)
                    else:
                        try:
                            result = process_method(datas)
                            message.write(
                                {
                                    "state": "done",
                                    "result": result.get("message"),
                                    "processed_hook_id": selected_hook.id,
                                }
                            )
                        except Exception as error:
                            message.write(
                                {
                                    "state": "error",
                                    "result": error,
                                    "processed_hook_id": selected_hook.id,
                                }
                            )

    @api.model
    def scan_queue_process(self):
        with registry(self.env.cr.dbname).cursor() as new_cr:
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            messages = self.with_env(new_env).search([("state", "=", "todo")])
            messages.process_messages()
