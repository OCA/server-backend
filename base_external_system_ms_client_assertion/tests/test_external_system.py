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
        system_type_oauth = self.env[ADAPTER_MODEL]
        with self.record.client() as client:
            self.assertEqual(client, system_type_oauth)
            # Client should have system_id property.
            self.assertEqual(client.system_id, self.record)

    def test_action_test_connection(self):
        """It should correctly connect to the remote system."""
        self.record.action_test_connection()
