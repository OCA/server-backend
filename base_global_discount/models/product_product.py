# Copyright 2023 Studio73 - Rafa Ferri <rafa.ferri@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    not_apply_global_discount = fields.Boolean(
        string="Don't apply global discount",
        help="If this checkbox is ticked, it means changing global discount on sale order "
        "won't impact sale order lines with this related product.",
    )
