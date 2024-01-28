# Copyright 2019 Tecnativa - David Vidal
# Copyright 2024 Sergio Zanchetta - PNLUG APS
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common


class TestGlobalDiscount(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.global_discount_obj = cls.env["global.discount"]
        cls.global_discount_1 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 1",
                "discount_scope": "sale",
                "discount_type": "percentage",
                "discount": 20,
            }
        )
        cls.global_discount_2 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 2",
                "discount_scope": "sale",
                "discount_type": "percentage",
                "discount": 30,
            }
        )
        cls.global_discount_3 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 3",
                "discount_scope": "sale",
                "discount_type": "fixed",
                "discount_fixed": 20,
            }
        )
        cls.global_discount_4 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 4",
                "discount_scope": "sale",
                "discount_type": "fixed",
                "discount_fixed": 40,
            }
        )

    def test_01_global_discounts(self):
        """Chain two different percentage discounts"""
        discount_vals = self.global_discount_1._get_global_discount_vals(100.0)
        self.assertAlmostEqual(discount_vals["base_discounted"], 80.0)
        discount_vals = self.global_discount_2._get_global_discount_vals(
            discount_vals["base_discounted"]
        )
        self.assertAlmostEqual(discount_vals["base_discounted"], 56.0)

    def test_02_display_name(self):
        """Test that the name is computed fine"""
        self.assertTrue("%)" in self.global_discount_1.display_name)

    def test_03_global_discounts(self):
        """Test fixed discounts"""
        discount_vals = self.global_discount_3._get_global_discount_vals(100.0)
        self.assertAlmostEqual(discount_vals["base_discounted"], 80.0)
        discount_vals = self.global_discount_4._get_global_discount_vals(
            discount_vals["base_discounted"]
        )
        self.assertAlmostEqual(discount_vals["base_discounted"], 40.0)

    def test_04_global_discounts(self):
        """Chain percentage and fixed discount types"""
        discount_vals = self.global_discount_2._get_global_discount_vals(100.0)
        self.assertAlmostEqual(discount_vals["base_discounted"], 70.0)
        discount_vals = self.global_discount_3._get_global_discount_vals(
            discount_vals["base_discounted"]
        )
        self.assertAlmostEqual(discount_vals["base_discounted"], 50.0)

    def test_05_display_name(self):
        """Test that the name is computed fine"""
        self.assertTrue(")" in self.global_discount_3.display_name)

    def test_06_discount_type_onchange(self):
        """Test discount type onchange"""
        self.global_discount_3.discount_type = "percentage"
        self.global_discount_3._onchange_discount()
        discount_fixed = self.global_discount_1.discount_fixed
        self.assertEqual(discount_fixed, 0.0)

    def test_07_discount_type_onchange(self):
        """Test discount type onchange"""
        self.global_discount_1.discount_type = "fixed"
        self.global_discount_1._onchange_discount()
        discount = self.global_discount_1.discount
        discount_base = self.global_discount_1.discount_base
        self.assertEqual(discount, 0.0)
        self.assertEqual(discount_base, "total")
