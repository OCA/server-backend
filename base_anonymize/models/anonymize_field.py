# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import json

from odoo import _, api, fields, models
from odoo.osv.expression import OR


class AnonymizeField(models.Model):
    _name = "anonymize.field"
    _description = "Field anonymization"
    _rec_name = "field_id"

    sequence = fields.Integer()
    active = fields.Boolean(default=True)

    model_name = fields.Char(required=True)
    field_name = fields.Char(required=True)

    model_id = fields.Many2one(
        "ir.model", compute="_compute_model_id", inverse="_inverse_model_id"
    )
    field_id = fields.Many2one(
        "ir.model.fields",
        domain="[('model_id', '=', model_id)]",
        compute="_compute_field_id",
        inverse="_inverse_model_id",
    )

    domain = fields.Char()

    applicable = fields.Boolean(
        compute="_compute_applicable", search="_search_applicable"
    )

    method = fields.Selection(selection="_selection_method", required=True)

    has_options = fields.Boolean(compute="_compute_has_options")
    options = fields.Text()
    options_display = fields.Html(compute="_compute_options_display")

    @api.depends("model_name")
    def _compute_model_id(self):
        for this in self:
            this.model_id = self.env["ir.model"]._get(this.model_name)

    @api.depends("model_name", "field_name")
    def _compute_field_id(self):
        for this in self:
            this.field_id = self.env["ir.model.fields"]._get(
                this.model_name, this.field_name
            )

    @api.depends("model_name", "field_name")
    def _compute_applicable(self):
        for this in self:
            this.applicable = (
                this.model_name in self.env
                and this.field_name in self.env[this.model_name]._fields
            )

    @api.depends("method")
    def _compute_has_options(self):
        for this in self:
            this.has_options = bool(this._get_options())

    @api.depends("options")
    def _compute_options_display(self):
        for this in self:
            options = this._get_options()
            if not options:
                this.options_display = False
            this.options_display = "<br />".join(
                "<b>"
                + self.env["ir.model.fields"]
                ._get(this.method, field_name)
                .field_description
                + f"</b> {str(value)[:17] + '...' if len(str(value)) > 19 else value}"
                for field_name, value in this._get_options().items()
            )

    @api.onchange("model_id")
    def _inverse_model_id(self):
        self.model_name = self.model_id.model

    @api.onchange("field_id")
    def _inverse_field_id(self):
        self.field_name = self.field_id.name

    @api.onchange("domain")
    def _onchange_domain(self):
        if not self.model_id:
            return
        try:
            self.env["anonymize.method"]._get_query(self)
        except Exception as e:
            return {
                "warning": {
                    "message": "".join(e.args or []),
                }
            }

    def _search_applicable(self, operator, value):
        assert operator == "=", "Only equality is supported"
        assert value, "Only truthy values are supported"
        return OR(
            [
                [
                    "&",
                    ("model_name", "=", model_name),
                    ("field_name", "in", list(self.env[model_name]._fields)),
                ]
                for model_name in self.env
            ]
        )

    def _selection_method(self):
        return [
            (model_name, self.env["ir.model"]._get(model_name).name)
            for model_name in self.env["anonymize.method"]._inherit_children
        ]

    def _get_options(self):
        self.ensure_one()
        options = json.loads(self.options or "{}")
        model = self.env[self.method or "base"]
        return {
            field_name: options.get(
                field_name,
                model._fields[field_name].default
                and model._fields[field_name].default(self),
            )
            for field_name in model._fields
            if field_name not in ("__last_update", "id", "display_name")
        }

    def action_options(self):
        self.ensure_one()
        context = {"active_id": self.id}
        options = self._get_options()
        context.update(
            {f"default_{field_name}": value for field_name, value in options.items()}
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Set options for %(display_name)s") % self,
            "res_model": self.method,
            "view_mode": "form",
            "target": "new",
            "context": context,
        }
