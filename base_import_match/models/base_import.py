# Copyright 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# Copyright 2016 Tecnativa - Vicent Cubells
# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class BaseImportMatchCacheMixin(models.AbstractModel):
    _name = "base_import.match.cache.mixin"
    _description = "Invalidate the _usable_rules cache on rule changes"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env.registry.clear_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res


class BaseImportMatch(models.Model):
    _name = "base_import.match"
    _inherit = "base_import.match.cache.mixin"
    _description = "Deduplicate settings prior to CSV imports."
    _order = "sequence, name"

    name = fields.Char(compute="_compute_name", store=True, index=True)
    sequence = fields.Integer(index=True)
    model_id = fields.Many2one(
        "ir.model",
        "Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
        help="In this model you will apply the match.",
    )
    model_name = fields.Char(
        string="Model name", related="model_id.model", store=True, index=True
    )
    field_ids = fields.One2many(
        comodel_name="base_import.match.field",
        inverse_name="match_id",
        string="Fields",
        required=True,
        help="Fields that will define an unique key.",
    )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.field_ids = False

    @api.depends("model_id", "field_ids")
    def _compute_name(self):
        """Automatic self-descriptive name for the setting records."""
        for one in self:
            display_names = one.field_ids.filtered("display_name").mapped(
                "display_name"
            )
            one.name = "{}: {}".format(
                one.model_id.display_name,
                " + ".join(display_names),
            )

    @api.model
    def _match_find(self, model, converted_row, imported_row):
        """Find a update target for the given row.

        This will traverse by order all match rules that can be used with the
        imported data, and return a match for the first rule that returns a
        single result.

        :param odoo.models.Model model:
            Model object that is being imported.

        :param dict converted_row:
            Row converted to Odoo api format, like the 3rd value that
            :meth:`odoo.models.Model._convert_records` returns.

        :param dict imported_row:
            Row as it is being imported, in format::

                {
                    "field_name": "string value",
                    "other_field": "True",
                    ...
                }

        :return odoo.models.Model:
            Return a dataset with one single match if it was found, or an
            empty dataset if none or multiple matches were found.
        """
        # Get usable rules to perform matches
        usable = self._usable_rules(model._name, converted_row)
        usable = self.browse(usable)
        # Traverse usable combinations
        for combination in usable:
            combination_valid = True
            domain = list()
            for field in combination.field_ids:
                # Check imported value if it is a conditional field
                if field.conditional:
                    # Invalid combinations are skipped
                    if imported_row[field.name] != field.imported_value:
                        combination_valid = False
                        break
                value = converted_row[field.name]
                # Converted many2one values come back as string ids, which would
                # never match an integer id in the domain (e.g. parent_id="32").
                model_field = model._fields.get(field.name)
                if (
                    model_field
                    and model_field.type == "many2one"
                    and isinstance(value, str)
                ):
                    value = int(value) if value else False
                domain.append((field.name, "=", value))
            if not combination_valid:
                continue
            match = model.search(domain)
            # When a single match is found, stop searching
            if len(match) == 1:
                return match
            elif match:
                _logger.warning(
                    "Found multiple matches for model %s and domain %s; "
                    "falling back to default behavior (create new record)",
                    model._name,
                    domain,
                )
        # Return an empty match if none or multiple was found
        return model

    @api.model
    @tools.ormcache("model_name", "frozenset(fields)")
    def _usable_rules(self, model_name, fields):
        """Return a set of elements usable for calling ``load()``.

        :param str model_name:
            Technical name of the model where you are loading data.
            E.g. ``res.partner``.

        :param list(str|bool) fields:
            List of field names being imported.

        :return bool:
            Indicates if we should patch its load method.
        """
        result = self
        # Relational columns are imported as "field/subfield" (e.g.
        # "parent_id/id"); compare against the field root so rules on those
        # fields are still recognized as usable.
        field_roots = {(f or "").split("/")[0] for f in fields}
        available = self.search([("model_name", "=", model_name)])
        # Use only criteria with all required fields to match
        for record in available:
            if all(f.name in field_roots for f in record.field_ids):
                result |= record
        return result.ids


class BaseImportMatchField(models.Model):
    _name = "base_import.match.field"
    _inherit = "base_import.match.cache.mixin"
    _description = "Field import match definition"

    name = fields.Char(related="field_id.name")
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Field",
        required=True,
        ondelete="cascade",
        domain="[('model_id', '=', model_id)]",
        help="Field that will be part of an unique key.",
    )
    match_id = fields.Many2one(
        comodel_name="base_import.match",
        string="Match",
        ondelete="cascade",
        required=True,
    )
    model_id = fields.Many2one(related="match_id.model_id")
    conditional = fields.Boolean(
        help="Enable if you want to use this field only in some conditions."
    )
    imported_value = fields.Char(
        help="If the imported value is not this, the whole matching rule will "
        "be discarded. Be careful, this data is always treated as a "
        "string, and comparison is case-sensitive so if you set 'True', "
        "it will NOT match '1' nor 'true', only EXACTLY 'True'."
    )

    @api.depends("conditional", "field_id", "imported_value")
    def _compute_display_name(self):
        for one in self:
            pattern = "{name} ({cond})" if one.conditional else "{name}"
            name = pattern.format(
                name=one.field_id.name,
                cond=one.imported_value,
            )
            one.display_name = name

    @api.onchange("field_id", "match_id", "conditional", "imported_value")
    def _onchange_match_id_name(self):
        """Update match name."""
        self.mapped("match_id")._compute_name()
