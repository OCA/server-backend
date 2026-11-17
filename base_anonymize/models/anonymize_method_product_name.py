# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models
from odoo.tools import SQL


class AnonymizeMethodProductName(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.product.name"
    _description = "Product name, or pattern without product"

    # for document line descriptions, which often quote the customer: the line
    # keeps the name of its product, lines without product get the pattern
    _default_options = {"pattern": "Line {id}"}

    def _run(self, field):
        model = self._get_model(field)
        if "product_id" not in model._fields:
            return 0
        table = SQL.identifier(model._table)
        template_name = SQL("product_template.name->>'en_US'")
        count = self._update(
            field,
            template_name,
            from_clause=SQL(
                "product_product JOIN product_template"
                " ON product_template.id = product_product.product_tmpl_id"
            ),
            where=SQL("product_product.id = %s.product_id", table),
        )
        count += self._update(
            field,
            SQL(
                "replace(%s, '{id}', %s.id::text)",
                field._get_options()["pattern"],
                table,
            ),
            where=SQL("%s.product_id IS NULL", table),
        )
        return count
