# Copyright 2019 Tecnativa - David Vidal
# Copyright 2022 Simone Rubino - TAKOBI
# Copyright 2024 Sergio Zanchetta - PNLUG APS
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class GlobalDiscount(models.Model):
    _name = 'global.discount'
    _description = 'Global Discount'
    _order = "sequence, id desc"

    sequence = fields.Integer(
        help='Gives the order to apply discounts',
    )
    name = fields.Char(
        string='Discount Name',
        required=True,
    )
    discount_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed'),
        ],
        default='percentage',
        required='True',
        string='Discount Type',
        help='Type of discount.',
    )
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
        default=0.0,
    )
    discount_fixed = fields.Float(
        string='Discount (Fixed)',
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    discount_base = fields.Selection(
        selection=[
            ('subtotal', 'Subtotal'),
            ('total', 'Total'),
        ],
        default='subtotal',
        required='True',
        string='Discount Base',
        help='Amount that will be discounted.',
    )
    discount_scope = fields.Selection(
        selection=[
            ('sale', 'Sales'),
            ('purchase', 'Purchases'),
        ],
        default='sale',
        required='True',
        string='Discount Scope',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )

#    @api.onchange('discount_type', 'discount_base')
    @api.onchange('discount_type')
    def _onchange_discount(self):
        if self.discount_type == 'percentage':
            self.discount_fixed = 0.0
        elif self.discount_type == 'fixed':
            self.discount = 0.0
            self.discount_base = 'total'

    def name_get(self):
        result = []
        for one in self:
            if one.discount_type == 'percentage':
                result.append(
                    (one.id, '{} ({:.2f}%)'.format(one.name, one.discount)))
            elif one.discount_type == 'fixed':
                result.append(
                    (one.id, '{} ({:.2f})'.format(one.name, one.discount_fixed)))
        return result

    def _get_global_discount_vals(self, base, **kwargs):
        """ Prepare the dict of values to create to obtain the discounted
            amount

           :param float base: the amount to discount
           :return: dict with the discounted amount
        """
        self.ensure_one()
        if self.discount_type == 'percentage':
            base_discounted = base * (1 - (self.discount / 100))
        elif self.discount_type == 'fixed':
            base_discounted = base - self.discount_fixed
        return {
            'global_discount': self,
            'base': base,
            'base_discounted': base_discounted,
        }
