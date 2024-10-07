# Copyright 2024 Therp BV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tests.common import TransactionCase

ADAPTER_MODEL = "external.system.adapter.ms.client.assertion"


class TestExternalSystem(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record = cls.env.ref(
            "base_external_system_ms_client_assertion"
            ".external_system_ms_client_assertion_demo"
        )

    def test_get_system_types(self):
        """It should return at least the test record's interface."""
        system_type_oauth = self.env[ADAPTER_MODEL]
        self.assertIn(
            (system_type_oauth._name, system_type_oauth._description),
            self.env["external.system"]._get_system_types(),
        )

    def test_client(self):
        """The client should be the adapter class."""
        # Would need to create a lot of mockup stuff to really test this.
