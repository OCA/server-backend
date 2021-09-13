# Copyright 2021 Le Filament (https://le-filament.com)
# Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.multi
    def write(self, vals):
        """
        This part of code comes from
        https://bazaar.launchpad.net/~eoc/openobject-server/
        + 6.1-overwrite_changes_translatable_fields/revision/4377

        When the main language in the company is not English, you cannot change
        the value of a translatable field in the table if you not switch the
        client interface to 'en_US', because the new value will be written
        to ir_translation table instead of the table model.

        This complicates usability, and the default language for "model" values
        hardcoded as 'en_US' should be configurable
        (see https://bugs.launchpad.net/openobject-server/+bug/400256).

        With this patch, all changes made in selected default language will be
        written in 'en_US' too (in the table model) if :
                  - vals are modified (it is later checked if vals are on
                        translatable fields)
                  - more than one language is installed
                  - default language is set
                  - current language = default language and not 'en_US'
        Also, translations in the other languages are changed to to_translate

        """
        result = super().write(vals)
        current_language = self.env.context.get("lang")
        default_language = (
            self.env["res.lang"].search(
                [("is_default_lang", "=", True), ("translatable", "=", True)], limit=1
            )
            or False
        )
        if (
            vals
            and len(self.env["res.lang"].get_installed()) > 1
            and default_language
            and current_language == default_language.code
            and current_language != "en_US"
        ):
            vals_en = {}
            for field in vals:
                if field in self._fields and self._fields[field].translate:
                    vals_en[field] = vals[field]
                    self._update_trans_status(
                        self._name, field, omit_langs=[default_language.code]
                    )
            if vals_en:
                super().with_context(lang="en_US").write(vals_en)
        return result

    def _update_trans_status(
        self, model, field, omit_langs=None, status="to_translate"
    ):
        """
        This function updates translations for this model / field / record (self)
        for all langs except omit_langs
        setting the state to status
        """
        langs = [code for code, _ in self.env["res.lang"].get_installed()]
        Translation = self.env["ir.translation"]
        translations = Translation.search(
            [
                ("type", "in", ("model", "model_terms")),
                ("name", "=", "%s,%s" % (model, field)),
                ("res_id", "=", self.id),
                ("lang", "in", langs),
                ("lang", "not in", omit_langs),
            ]
        )
        for translation in translations:
            translation.state = status
