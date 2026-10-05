from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ExternalRecordMapped(models.AbstractModel):
    """Provides utilities for mapping multiple external records to a single one"""

    _name = "base.external.record.mapped"
    _description = "Mixin for mapping models"

    _rec_names_search = ["external_name", "external_key"]
    _check_company_auto = True
    _external_key_name = False

    external_name = fields.Char()
    external_key = fields.Char(index="btree_not_null", required=True)
    external_table = fields.Char(index=True)
    mapped_key = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="cascade",
        default=False,
        index=True,
    )
    record_model = fields.Char("Resource Model")
    record_id = fields.Many2oneReference(
        "Record ID",
        model_field="record_model",
        compute="_compute_record_id",
        store=True,
    )
    sql_constraints = [
        (
            "external_unique",
            "UNIQUE(external_key, company_id)",
            "External keys must be unique per company!",
        ),
    ]

    @api.constrains("external_key", "mapped_key", "record_model")
    def _check_mapped_key_not_in_external_keys(self):
        for record in self:
            if self.search_count(
                [
                    ("external_key", "=", record.mapped_key),
                    ("id", "!=", record.id),
                    ("record_model", "=", record.record_model),
                ]
            ):
                raise ValidationError(
                    self.env._(
                        "Target key %(key)s is the source of another mapping",
                        key=record.mapped_key,
                    )
                )

            if self.search_count(
                [
                    ("mapped_key", "=", record.external_key),
                    ("id", "!=", record.id),
                    ("record_model", "=", record.record_model),
                ]
            ):
                raise ValidationError(
                    self.env._(
                        "Source key %(key)s is the target of another mapping",
                        key=record.external_key,
                    )
                )

    @api.depends("mapped_key", "record_model")
    def _compute_record_id(self):
        for record in self:
            target = (
                self.env[record.record_model]
                .with_context(active_test=False)
                .search([(self._external_key_name, "=", record.mapped_key)])
            )
            if len(target) != 1:
                record.record_id = record.record_id
                continue
            record.record_id = target.id

    @api.model
    def ensure_mapping(self, vals):
        existing = self.search(
            [
                ("external_key", "=", vals["external_key"]),
                ("record_model", "=", vals["record_model"]),
                ("company_id", "=", vals.get("company_id")),
            ]
        )
        if existing:
            existing.mapped_key = vals["mapped_key"]
            return existing
        return self.create(vals)

    @api.model
    def is_mapped(self, model, key):
        return bool(
            self.search_count(
                [
                    ("record_model", "=", model),
                    ("external_key", "=", key),
                ],
                limit=1,
            )
        )
