# Copyright 2020 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

from odoo import api, fields, models
from odoo.tools import pycompat
from odoo.tools.safe_eval import safe_eval


class ExportMassiveTranslation(models.TransientModel):
    _name = "export.massive.translation"
    _description = "Export Massive Translations Template"

    name = fields.Char(string="File Name", readonly=True,)
    data = fields.Binary(string="File", readonly=True, attachment=False)
    state = fields.Selection(
        string="State",
        selection=[("choose", "choose"), ("get", "get")],
        default="choose",
    )
    translated_model = fields.Many2one(
        string="Model",
        comodel_name="ir.model",
        help="Model you want to get the terms to translate from.",
        domain=[("transient", "=", False)],
        required=True,
    )
    translated_model_name = fields.Char(
        string="Translated Model Name", related="translated_model.model",
    )
    reference_field = fields.Many2one(
        string="Reference Field",
        comodel_name="ir.model.fields",
        help="Second column of the file. It contains a field to use as a \
        reference of the record the user is working on.",
    )
    translated_fields = fields.Many2many(
        string="Fields",
        comodel_name="ir.model.fields",
        help="Fields from the model you want to translate.",
    )
    languages = fields.Many2many(
        string="Languages",
        comodel_name="res.lang",
        default=lambda self: self._default_languages(),
        help="Languages you want to translate terms into.",
    )
    record_selection = fields.Selection(
        selection=[("all", "All Records"), ("domain", "Domain")],
        string="Records",
        required=True,
        default="all",
        help="Show all translatable records on the template or select a \
        domain.",
    )
    record_domain = fields.Char(string="Domain", default=[("name", "ilike", "")])
    show_translated = fields.Boolean(
        string="Show Translated Terms",
        default=True,
        help="Check if the template has to contain both the fields that have \
        already been translated and those that have not been translated yet.",
    )

    @api.onchange("translated_model")
    def _domain_translated_fields(self):
        res_translated = {}
        if self.translated_model:
            res_translated.update(
                domain={
                    "translated_fields": [
                        ("translate", "=", True),
                        ("compute", "=", False),
                        ("depends", "=", False),
                        ("related", "=", False),
                        ("model_id", "=", self.translated_model.id),
                        (
                            "ttype",
                            "not in",
                            (
                                "many2many",
                                "many2one",
                                "many2one_reference",
                                "one2many",
                                "reference",
                            ),
                        ),
                    ]
                }
            )
        return res_translated

    @api.onchange("translated_model")
    def _domain_reference_fields(self):
        res_reference = {}
        if self.translated_model:
            res_reference.update(
                domain={
                    "reference_field": [
                        ("model_id", "=", self.translated_model.id),
                        ("ttype", "in", ("char", "text")),
                    ]
                }
            )
        return res_reference

    def _default_languages(self):
        return self.env["res.lang"].search([]).ids

    def get_filename(self):
        return "import_product_translations_template.csv"

    def _get_ref_field(self):
        ref_field = ""
        if self.reference_field:
            ref_field = self.reference_field.name
        else:
            ref_field = self.translated_model._rec_name or "name"
        return ref_field

    def get_file(self):
        self.ensure_one()
        ref_field = self._get_ref_field()

        languages_codes = self.languages.mapped("code")

        # Contains the set of document lines
        final_lines = []
        header = ["id", ("%s#reference" % ref_field)]
        for field in self.translated_fields:
            header.append("%s#origin" % field.name)
            for language in languages_codes:
                header.append("{}#{}".format(field.name, language))
        final_lines.append(header)

        dom = [] if self.record_selection == "all" else safe_eval(self.record_domain)
        instances_ids = self.env[self.translated_model.model].search(dom)

        # Include all the record id's and all the values of reference field
        final_lines.extend([[i.id, getattr(i, ref_field) or ""] for i in instances_ids])

        for field in self.translated_fields:
            # Origin values
            row = 0
            for i in instances_ids:
                row += 1
                final_lines[row].append(
                    getattr(i.with_context(lang=""), str(field.name)) or ""
                )
            # Translation of a field in each language
            for language in languages_codes:
                translations = self.env["ir.translation"]._get_ids(
                    "{},{}".format(self.translated_model.model, field.name),
                    "model",
                    language,
                    instances_ids.ids,
                )
                row = 0
                for i in instances_ids:
                    row += 1
                    final_lines[row].append(translations.get(i.id) or "")

        if not self.show_translated:
            for line in filter(lambda x: "" not in x, final_lines[1:]):
                final_lines.remove(line)

        # Generation of BytesIO with codification from string to bytes
        bio = io.BytesIO()
        writer = pycompat.csv_writer(bio, quoting=1)
        for line in final_lines:
            writer.writerow(line)
        out = base64.encodestring(bio.getvalue())
        name = self.get_filename()
        self.write({"state": "get", "data": out, "name": name})
        return {
            "type": "ir.actions.act_window",
            "res_model": "export.massive.translation",
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }
