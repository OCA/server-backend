# Copyright 2020 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import csv
from io import StringIO

from odoo import _, exceptions, fields, models


class ImportMassiveTranslation(models.TransientModel):
    _name = "import.massive.translation"
    _description = "Import Massive Translation"

    data = fields.Binary(
        string="File",
        required=True,
        helper="Upload a template with the translations terms.",
    )
    translated_model = fields.Many2one(string="Model", comodel_name="ir.model",)
    delimeter = fields.Char(string="Delimiter", default=",", required=True,)

    def _field_exists(self, field):
        if not self.translated_model.field_id.search([("name", "=", field)], limit=1):
            raise exceptions.ValidationError(
                _("%s is not a valid field in %s model")
                % (field, self.translated_model.model)
            )
        else:
            return True

    def _language_exists(self, language):
        if not self.env["res.lang"].search(
            [("code", "=", language), ("active", "=", True)], limit=1
        ):
            raise exceptions.ValidationError(
                _("%s is not an active language.") % language
            )
        else:
            return True

    def _check_keys(self, keys):

        # First column: ID
        i = 0
        if keys[i] != "id":
            raise exceptions.ValidationError(_("The first key needs to be id"))

        # Second column: Reference
        i += 1
        reference_key = keys[i]
        reference_key_field = reference_key.split("#")[0]
        model_field = self._field_exists(reference_key_field)
        if not model_field or reference_key.split("#")[1] != "reference":
            raise exceptions.ValidationError(
                _(
                    "The second key needs to be the reference field with format \
                valid_field#reference"
                )
            )

        # Find duplicates
        duplicated_keys = list({x for x in keys if keys.count(x) > 1})
        if duplicated_keys:
            raise exceptions.ValidationError(
                _("%s keys cannot be duplicated.") % duplicated_keys
            )

        # Not empty keys
        if any("" == x for x in keys):
            raise exceptions.ValidationError(_("Empty keys found"))

    def _check_origin(self, keys, fields):
        origin_error = list(filter(lambda x: ("%s#origin" % x) not in keys, fields))
        if origin_error:
            raise exceptions.ValidationError(
                _(
                    "All fields need an origin key. %s#origin key needed but not \
                found"
                )
                % origin_error
            )

    def _check_ids(self, values):
        used_ids = []
        for i in values:
            try:
                val_id = int(i)
                used_ids.append(val_id)
            except Exception:
                raise exceptions.ValidationError(_("Invalid ID found: %s" % i))
        # IDs need to be valid in the selected model
        found_ids = (
            self.env[self.translated_model.model].search([("id", "in", used_ids)]).ids
        )
        # Some IDs do not exist in the model
        difference_ids = list(set(used_ids) - set(found_ids))
        if difference_ids:
            raise exceptions.Warning(
                _(
                    "The following IDs do not exist in the \
                system: %s"
                    % difference_ids
                )
            )
        return used_ids

    def get_translation_by_language(self, field, language, values):
        search_domain = [
            ("type", "=", "model"),
            ("name", "=", "{},{}".format(self.translated_model.model, field)),
            ("res_id", "=", values["id"]),
            ("lang", "=", language),
        ]
        translation = self.env["ir.translation"].search((search_domain), limit=1)
        return translation

    def get_translations_by_source(self, field, source, values):
        translations = self.env["ir.translation"].search(
            [
                ("type", "=", "model"),
                ("name", "=", "{},{}".format(self.translated_model.model, field)),
                ("res_id", "=", values["id"]),
                ("src", "=", source),
            ]
        )
        return translations

    def modify_origin_field(self, field, values):
        rec = self.env[self.translated_model.model].browse(int(values.get("id")))
        val = values.get("%s#origin" % field)
        old_term = getattr(rec.with_context(lang=""), field)
        if old_term != val:
            rec.with_context(lang="").write({field: val})

    def get_translation_terms(self, field, language, values):
        translation_terms = {
            "src": values[field + "#origin"],
            "value": values[field + "#" + language],
            "name": self.translated_model.model + "," + field,
            "lang": language,
            "type": "model",
            "state": "translated",
            "res_id": values["id"],
        }
        return translation_terms

    def get_term_dictionary(self, values, field, language):
        return {
            "name": self.translated_model.model + "," + field,
            "lang": language,
            "res_id": values["id"],
            "src": values[field + "#origin"],
            "type": "model",
            "value": values[field + "#" + language],
            "state": "translated",
        }

    def action_import(self):
        """Load the CSV file."""
        if not self.data:
            raise exceptions.Warning(_("No file selected"))
        data = base64.b64decode(self.data).decode("utf-8")
        file_input = StringIO(data)
        file_input.seek(0)
        reader_info = []
        reader = csv.DictReader(
            file_input, delimiter=self.delimeter, lineterminator="\r\n",
        )
        try:
            # Extend the list
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Not a valid file"))

        # Keys selected and checked
        keys = reader.fieldnames
        self._check_keys(keys)

        # Record IDs are selected and checked
        records_ids = self._check_ids([x["id"] for x in reader_info])

        # Languages and fields contained in the template
        # are selected and checked
        languages = []
        fields = []
        for key in filter(
            lambda x: "#" in x and x.split("#")[1] not in ("reference", "origin"), keys
        ):
            new_field = key.split("#")[0]
            new_language = key.split("#")[1]
            if new_field not in fields:
                self._field_exists(new_field)
                fields.append(new_field)
            if new_language not in languages:
                self._language_exists(new_language)
                languages.append(new_language)

        self._check_origin(keys, fields)

        # Modify origin fields
        for r in reader_info:
            for field in filter(lambda x: r["%s#origin" % x], fields):
                self.modify_origin_field(field, r)

        # List to contain the diccionaries with values of the translations
        # fields that need to be created or modified
        create_modify_records = []
        for field in fields:
            for language in languages:
                translations = self.env["ir.translation"]._get_ids(
                    "{},{}".format(self.translated_model.model, field),
                    "model",
                    language,
                    records_ids,
                )
                for i in filter(
                    lambda x: x.get("{}#{}".format(field, language))
                    and translations.get(int(x.get("id")))
                    != x.get("{}#{}".format(field, language))
                    or translations.get(int(x.get("id"))) is None,
                    reader_info,
                ):
                    term_dictionary = self.get_term_dictionary(i, field, language)
                    create_modify_records.append(term_dictionary)

        # Translation lines are created or modified
        self.env["ir.translation"]._upsert_translations(create_modify_records)

        return {"type": "ir.actions.act_window_close"}
