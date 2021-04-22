# Copyright 2017 LasLabs Inc.
# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestExternalSystem(TransactionCase):
    def setUp(self):
        super().setUp()
        self.record = self.env.ref("base_external_system.external_system_os")

    def test_check_fingerprint_blank(self):
        """It should not allow blank fingerprints when checking enabled."""
        with self.assertRaises(ValidationError):
            self.record.write({"ignore_fingerprint": False, "fingerprint": False})

    def test_check_fingerprint_allowed(self):
        """It should not raise a validation error if there is a fingerprint."""
        # In Odoo 13.0, due to the way inverse records (models inherited from)
        # are handled, setting both fields at the same time causes an error.
        self.record.write({"fingerprint": "Data"})
        self.record.write({"ignore_fingerprint": False})
        self.assertTrue(True)

    def test_action_test_connection(self):
        """It should proxy to the interface connection tester."""
        # As the connection for his adapter should always succeed, just call it...
        self.record.action_test_connection()
