# Copyright (C) 2021 Daniel Reis
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase


class TestPipInstall(TransactionCase):
    def test_get_pypi_package_name(self):
        module_name = "mis_builder"
        pkg_name = self.env["ir.module.module"]._get_pypi_package_name(module_name)
        self.assertEqual(pkg_name, "odoo14-addon-mis-builder")
