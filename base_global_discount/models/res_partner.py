# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_global_discount_ids = fields.Many2many(
        comodel_name='global.discount',
        column1='partner_id',
        column2='global_discount_id',
        string='Sale Global Discounts',
        domain=[('discount_scope', '=', 'sale')],
    )
    supplier_global_discount_ids = fields.Many2many(
        comodel_name='global.discount',
        column1='partner_id',
        column2='global_discount_id',
        string='Purchase Global Discounts',
        domain=[('discount_scope', '=', 'purchase')],
    )
    # HACK: Looks like UI doesn't behave well with Many2many fields and
    # negative groups when the same field is shown. In this case, we want to
    # show the readonly version to any not in the global discount group.
    # TODO: Check if it's fixed in future versions
    customer_global_discount_ids_readonly = fields.Many2many(
        related="customer_global_discount_ids",
        readonly=True,
        string='Sale Global Discounts (Readonly)',
    )
    supplier_global_discount_ids_readonly = fields.Many2many(
        related="supplier_global_discount_ids",
        readonly=True,
        string='Purchase Global Discounts (Readonly)',
    )
