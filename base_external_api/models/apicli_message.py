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

    def content_convert(self, endpoint, content):
        data = {}
        file_extension = endpoint.split(".") and endpoint.split(".")[-1] or None
        if file_extension == "xml":
            # XML data convert to dict.
            data = json.dumps(xmltodict.parse(content))
        elif file_extension == "json":
            # JSON data convert to dict.
            data = json.loads(content)
        return data

    @api.model
    def scan_queue_process(self):
        for message in self.search([("state", "=", "todo")]):
            selected_hook = False
            for hook in self.env["apicli.hook"].search(
                [("method_name", "!=", False), ("model_id", "!=", False)]
            ):
                content_match = re.search(hook.match_regexp, message.endpoint, re.I)
                if content_match:
                    selected_hook = hook
                    break
            if selected_hook:
                ref_function = getattr(
                    self.env[selected_hook.model_id.model],
                    "{}".format(selected_hook.method_name),
                )
                if ref_function:
                    datas = {
                        "endpoint": message.endpoint,
                        "raw": message.content,
                        "parsed": self.content_convert(
                            message.endpoint, message.content
                        ),
                    }
                    ref_function(datas)
        return True
