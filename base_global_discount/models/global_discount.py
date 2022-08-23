# Copyright 2019 Tecnativa - David Vidal
# Copyright 2022 Simone Rubino - TAKOBI
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
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
    discount = fields.Float(
        digits=dp.get_precision('Discount'),
        required=True,
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

    def name_get(self):
        result = []
        for one in self:
            result.append(
                (one.id, '{} ({:.2f}%)'.format(one.name, one.discount)))
        return result

    def _get_global_discount_vals(self, base, **kwargs):
        """ Prepare the dict of values to create to obtain the discounted
            amount

           :param float base: the amount to discount
           :return: dict with the discounted amount
        """
        self.ensure_one()
        return {
            'global_discount': self,
            'base': base,
            'base_discounted': base * (1 - (self.discount / 100)),
        }
