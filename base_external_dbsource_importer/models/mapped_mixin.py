from odoo import api, fields, models


class DbsourceExternalMixin(models.AbstractModel):
    """Provides utilities for mapping multiple external records to a single one"""

    _name = "dbsource.mapped.mixin"
    _description = "Mixin for mapping models"

    _rec_names_search = ["external_name", "external_key"]
    _check_company_auto = True

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

    @api.depends("mapped_key", "record_model")
    def _compute_record_id(self):
        for record in self:
            target = (
                self.env[record.record_model]
                .with_context(active_test=False)
                .search([("openbravo_key", "=", record.mapped_key)])
            )
            if len(target) != 1:
                record.record_id = record.record_id
                continue
            record.record_id = target.id
