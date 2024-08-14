# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common


class TestGlobalDiscount(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.global_discount_obj = cls.env["global.discount"]
        cls.global_discount_1 = cls.global_discount_obj.create(
            {"name": "Test Discount 1", "discount_scope": "sale", "discount": 20}
        )
        cls.global_discount_2 = cls.global_discount_obj.create(
            {"name": "Test Discount 2", "discount_scope": "sale", "discount": 30}
        )

    def test_01_global_discounts(self):
        """Chain two discounts of different types"""
        discount_vals = self.global_discount_1._get_global_discount_vals(100.0)
        self.assertAlmostEqual(discount_vals["base_discounted"], 80.0)
        discount_vals = self.global_discount_2._get_global_discount_vals(
            discount_vals["base_discounted"]
        )
        self.assertAlmostEqual(discount_vals["base_discounted"], 56.0)

    def test_02_display_name(self):
        """Test that the name is computed fine"""
        self.assertTrue("%)" in self.global_discount_1.display_name)

    def test_03_bypass_products(self):
        template_obj = self.env["product.template"]
        template = template_obj.create({"name": "Test Template"})
        template.bypass_global_discount = True
        self.assertTrue(template.bypass_global_discount)
        search_result = template._search_bypass_global_discount("=", True)
        self.assertEqual(len(search_result), 1)
        self.assertEqual(template.id, search_result[0][2][0])
