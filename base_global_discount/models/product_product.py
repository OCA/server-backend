# Copyright 2024 Studio73 - Ferran Mora <ferran@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    bypass_global_discount = fields.Boolean(
        string="Don't apply global discount",
        help=(
            "If this checkbox is ticked, it means that this product will not be taken "
            "into account when calculating the global discounts."
        ),
    )
