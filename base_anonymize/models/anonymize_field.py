# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import json
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import OR
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class AnonymizeField(models.Model):
    _name = "anonymize.field"
    _description = "Field anonymization"
    _rec_name = "field_name"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
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
        inverse="_inverse_field_id",
    )

    domain = fields.Char(
        help="Restrict the records to overwrite. Evaluated with the variables "
        "protected_partner_ids (partners of the companies, OdooBot and the public "
        "users), admin_user_ids (superuser and administrator) and "
        "protected_user_ids (the same plus the public users)."
    )

    applicable = fields.Boolean(
        compute="_compute_applicable", search="_search_applicable"
    )

    method = fields.Selection(selection="_selection_method", required=True)

    options = fields.Text(help="JSON object overriding the method's default options")
    default_options = fields.Text(compute="_compute_default_options")

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

    def _inverse_model_id(self):
        for this in self:
            this.model_name = this.model_id.model

    def _inverse_field_id(self):
        for this in self:
            this.field_name = this.field_id.name

    @api.depends("model_name", "field_name")
    def _compute_applicable(self):
        for this in self:
            this.applicable = (
                this.model_name in self.env
                and this.field_name in self.env[this.model_name]._fields
            )

    def _search_applicable(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise NotImplementedError(_("Unsupported search on applicable"))
        domain = OR(
            [
                [
                    "&",
                    ("model_name", "=", model_name),
                    ("field_name", "in", list(self.env[model_name]._fields)),
                ]
                for model_name in self.env
            ]
        )
        if (operator == "=") != value:
            return ["!"] + domain
        return domain

    @api.depends("method")
    def _compute_default_options(self):
        for this in self:
            defaults = this.method and self.env[this.method]._default_options or {}
            this.default_options = json.dumps(defaults) if defaults else False

    def _selection_method(self):
        return [
            (model_name, self.env[model_name]._description)
            for model_name in sorted(self.env["anonymize.method"]._inherit_children)
        ]

    @api.constrains("options")
    def _check_options(self):
        for this in self:
            if not this.options:
                continue
            try:
                options = json.loads(this.options)
            except ValueError as e:
                raise ValidationError(_("Options must be valid JSON: %s", e)) from e
            if not isinstance(options, dict):
                raise ValidationError(_("Options must be a JSON object"))

    @api.constrains("domain", "model_name")
    def _check_domain(self):
        for this in self:
            if this.domain and this.model_name in self.env:
                try:
                    self.env["anonymize.method"]._get_query(this)
                except Exception as e:
                    raise ValidationError(
                        _("Invalid domain for %(model)s: %(error)s")
                        % {"model": this.model_name, "error": e}
                    ) from e

    def _get_options(self):
        self.ensure_one()
        options = dict(self.env[self.method]._default_options)
        options.update(json.loads(self.options or "{}"))
        return options

    def _get_domain(self):
        self.ensure_one()
        if not self.domain:
            return []
        env = self.env(su=True)
        companies = env["res.company"].with_context(active_test=False).search([])
        public_users = (
            env.ref("base.public_user", raise_if_not_found=False) or env["res.users"]
        )
        if "website" in env:
            websites = env["website"].with_context(active_test=False).search([])
            public_users |= websites.user_id
        partner_root = (
            env.ref("base.partner_root", raise_if_not_found=False) or env["res.partner"]
        )
        admin_user_ids = [
            env.ref(xmlid).id
            for xmlid in ("base.user_root", "base.user_admin")
            if env.ref(xmlid, raise_if_not_found=False)
        ]
        return safe_eval(
            self.domain,
            {
                "protected_partner_ids": (
                    companies.partner_id | public_users.partner_id | partner_root
                ).ids,
                "admin_user_ids": admin_user_ids,
                "protected_user_ids": admin_user_ids + public_users.ids,
            },
        )

    def _check_neutralized(self):
        """Refuse to overwrite a database that was not neutralized: the
        parameter is set by odoo-bin neutralize, by the database manager when it
        neutralizes a copy, and on staging builds of Odoo.sh."""
        neutralized = (
            self.env["ir.config_parameter"].sudo().get_param("database.is_neutralized")
        )
        if not neutralized:
            raise UserError(
                _(
                    "This database was not neutralized. Anonymization overwrites "
                    "data irreversibly and only runs on neutralized copies: "
                    "run odoo-bin neutralize on the copy first."
                )
            )

    def _run(self):
        """Run the definitions in self, in sequence. Never on production data."""
        self._check_neutralized()
        definitions = self.filtered("applicable")
        xmlids = definitions.get_external_id()
        started = time.monotonic()
        for this in definitions:
            step = time.monotonic()
            count = self.env[this.method]._run(this)
            _logger.info(
                "Anonymized %s.%s with %s (%s, domain %s): %s rows in %.1fs",
                this.model_name,
                this.field_name,
                this.method,
                xmlids.get(this.id) or f"anonymize.field {this.id}",
                this.domain or "[]",
                count,
                time.monotonic() - step,
            )
            # the methods write in SQL behind the ORM's back
            self.env.invalidate_all()
        # files of attachments whose content was dropped
        self.env["ir.attachment"]._gc_file_store_unsafe()
        _logger.info(
            "Anonymization done: %s definitions in %.1fs",
            len(definitions),
            time.monotonic() - started,
        )
        return True

    @api.model
    def _run_all(self):
        return self.search([("applicable", "=", True)])._run()
