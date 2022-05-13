# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import datetime
import logging

import jinja2
from lxml import etree

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ApicliDocument(models.Model):
    _name = "apicli.document"
    _description = "Document"
    _order = "sequence"
    _description = "API Document template"

    name = fields.Char("Document", required=True)
    sequence = fields.Integer()
    code = fields.Char(index=True)
    model_id = fields.Many2one("ir.model", ondelete="cascade", required=True)
    file_type = fields.Selection(
        [("json", "JSON"), ("xml", "XML"), ("txt", "TXT")],
        default="xml",
    )
    endpoint = fields.Char()
    template_view_id = fields.Many2one("ir.ui.view", domain=[("type", "=", "qweb")])
    template_text = fields.Text()
    validation_text = fields.Text()
    header = fields.Text()

    @api.model
    def get_document(self, model=None, code=None):
        domain = []
        if model:
            domain.append(("model_id.model", "=", model))
        if code:
            domain.append(("code", "=", code))
        return self.search(domain, limit=1)

    def render(self, recordset):
        self.ensure_one()  # TODO: support many docs?
        endpoint = self._render_endpoint(recordset)
        document = self._render_template(recordset)
        self._validate_document(document)
        return {endpoint: document}

    def _get_render_context(self, recordset):
        return {
            "o": recordset,
            "doc": recordset,
            "docs": recordset,
            "self": recordset,
            "now": fields.datetime.now,
            "today": fields.datetime.today,
            "date": datetime.date,
            "datetime": datetime.datetime,
            "timedelta": datetime.timedelta,
            "float": float,
            "int": int,
            "str": str,
        }

    def _render_jinja_template(self, recordset, template_text):
        """
        In: self recordset and template string
        Out: string with the processed template
        """
        jinja_env = jinja2.Environment(
            lstrip_blocks=True, trim_blocks=True, loader=jinja2.BaseLoader()
        )
        template = jinja_env.from_string(template_text)
        values = self._get_render_context(recordset)
        res = template.render(values)
        return res

    def _render_endpoint(self, recordset):
        self.ensure_one()
        if self.endpoint:
            return self._render_jinja_template(recordset, self.endpoint)

    def _render_template(self, recordset):
        if self.template_text:
            res = self._render_jinja_template(recordset, self.template_text)
        else:
            values = self._get_render_context(recordset)
            res = self.template_view_id._render(values)
        return str(res)

    def _validate_document(self, file_text):
        validations = self.filtered(
            lambda x: x.file_type == "xml" and x.validation_text
        )
        for tmpl in validations:
            validator = tmpl.validation_text
            xmlschema = etree.XMLSchema(validator)
            xml_doc = etree.fromstring(file_text)
            result = xmlschema.validate(xml_doc)
            if not result:
                # try:
                xmlschema.assert_(xml_doc)
                # FIXME: delete?
                # except AssertionError as e:
                #     _logger.warning(etree.tostring(xml_doc))
                #     raise UserError(_("XML Malformed Error: %s") % e.args)
