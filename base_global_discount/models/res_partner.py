# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    customer_global_discount_ids = fields.Many2many(
        comodel_name="global.discount",
        relation="customer_global_discount_rel",
        column1="partner_id",
        column2="global_discount_id",
        string="Sale Global Discounts",
        domain=[("discount_scope", "=", "sale")],
    )
    supplier_global_discount_ids = fields.Many2many(
        comodel_name="global.discount",
        relation="supplier_global_discount_rel",
        column1="partner_id",
        column2="global_discount_id",
        string="Purchase Global Discounts",
        domain=[("discount_scope", "=", "purchase")],
    )
    # HACK: Looks like UI doesn't behave well with Many2many fields and
    # negative groups when the same field is shown. In this case, we want to
    # show the readonly version to any not in the global discount group.
    # TODO: Check in v14 if it's fixed
    customer_global_discount_ids_readonly = fields.Many2many(
        string="Sale Global Discounts (readonly)",
        related="customer_global_discount_ids",
        readonly=True,
    )
    supplier_global_discount_ids_readonly = fields.Many2many(
        string="Purchase Global Discounts (readonly)",
        related="supplier_global_discount_ids",
        readonly=True,
    )
