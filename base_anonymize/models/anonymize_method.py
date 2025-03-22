# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import json

from lxml import etree

from odoo import _, api, models
from odoo.osv.expression import expression
from odoo.tools.safe_eval import const_eval


class AnonymizeMethod(models.AbstractModel):
    _name = "anonymize.method"
    _description = "Anonymization method"
    _auto = False

    def _run(self, field):
        raise NotImplementedError()

    def _get_query(self, field):
        expr = expression(
            field.domain and const_eval(field.domain) or [],
            self.env[field.model_id.model].with_context(active_test=False),
        )
        return expr.query.get_sql()

    @api.model_create_single
    def create(self, vals):  # pylint: disable=method-required-super
        self.env["anonymize.field"].browse(self.env.context.get("active_id", [])).write(
            {"options": json.dumps(vals)}
        )
        return self

    def read(self, fields=None):  # pylint: disable=method-required-super
        return [{"id": _id} for _id in self._ids]

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        return True

    @api.model
    def _fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super()._fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        arch = etree.fromstring(result["arch"])
        if not arch.xpath("//footer"):
            footer = etree.SubElement(arch, "footer")
            etree.SubElement(
                footer,
                "button",
                {
                    "name": "action_nothing",
                    "type": "object",
                    "string": _("Save"),
                    "class": "btn-primary",
                },
            )
            etree.SubElement(
                footer, "button", {"special": "cancel", "string": _("Discard")}
            )
        result["arch"] = etree.tostring(arch)
        return result

    def action_nothing(self):
        pass
