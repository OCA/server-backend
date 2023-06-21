# Copyright 2023 Studio73 - Rafa Ferri <rafa.ferri@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    apply_global_discount = fields.Boolean(
        string="Apply global discount",
        search="_search_apply_discount_apply",
        compute="_compute_apply_discount_apply",
        inverse="_inverse_apply_discount_apply",
        help="If this checkbox is ticked, it means changing global discount on sale order "
        "will impact sale order lines with this related product.",
    )

    def _search_apply_discount_apply(self, operator, value):
        templates = self.with_context(active_test=False).search(
            [("product_variant_ids.apply_global_discount", operator, value)]
        )
        return [("id", "in", templates.ids)]

    @api.depends("product_variant_ids.apply_global_discount")
    def _compute_apply_discount_apply(self):
        self.apply_global_discount = True
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.apply_global_discount = (
                    template.product_variant_ids.apply_global_discount
                )

    def _inverse_apply_discount_apply(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.apply_global_discount = self.apply_global_discount
