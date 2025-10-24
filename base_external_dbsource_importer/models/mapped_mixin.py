from odoo import fields, models


class DbsourceExternalMixin(models.AbstractModel):
    """Provides utilities for mapping multiple external records to a single one"""

    _name = "dbsource.mapped.mixin"
    _description = "Mixin for mapping models"

    _rec_names_search = ["external_name", "external_key"]
    _check_company_auto = True

    external_name = fields.Char()
    external_key = fields.Char()
    mapped_key = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="cascade",
        default=lambda self: self.env.company,
        index=True,
    )

    sql_constraints = [
        (
            "external_unique",
            "UNIQUE(external_key, company_id)",
            "External keys must be unique per company!",
        ),
    ]
