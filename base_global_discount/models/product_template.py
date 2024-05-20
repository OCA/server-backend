# Copyright 2024 Studio73 - Ferran Mora <ferran@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bypass_global_discount = fields.Boolean(
        string="Don't apply global discount",
        help=(
            "If this checkbox is ticked, it means that this product will not be taken "
            "into account when calculating the global discounts."
        ),
        compute="_compute_bypass_global_discount",
        inverse="_inverse_bypass_global_discount",
    )

    def _search_bypass_global_discount(self, operator, value):
        templates = self.with_context(active_test=False).search(
            [("product_variant_ids.bypass_global_discount", operator, value)]
        )
        return [("id", "in", templates.ids)]

    @api.depends("product_variant_ids.bypass_global_discount")
    def _compute_bypass_global_discount(self):
        self.bypass_global_discount = False
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.bypass_global_discount = (
                    template.product_variant_ids.bypass_global_discount
                )

    def _inverse_bypass_global_discount(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.bypass_global_discount = (
                self.bypass_global_discount
            )
