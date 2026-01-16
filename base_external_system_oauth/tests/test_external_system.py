from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

ADAPTER_MODEL = "external.system.adapter.oauth"


class _FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


class TestExternalSystem(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record = cls.env.ref(
            "base_external_system_oauth.external_system_oauth_demo"
        )
        cls.record.oauth_definition_id.write({"client_secret": "the-secret"})

    def test_get_system_types(self):
        """It should return at least the test record's interface."""
        system_type_oauth = self.env[ADAPTER_MODEL]
        self.assertIn(
            (system_type_oauth._name, system_type_oauth._description),
            self.env["external.system"]._get_system_types(),
        )

    def test_client(self):
        """The client should be an interface record of the OAuth adapter."""
        with self.record.client() as client:
            self.assertEqual(client._name, ADAPTER_MODEL)
            # Client should point back to the external.system.
            self.assertEqual(client.system_id, self.record)

    def test_action_test_connection(self):
        """It should correctly connect to the remote system."""
        # The base HTTP adapter performs a GET to the base URL. Patch the
        # underlying requests.get used in that module so we don't do network I/O.
        with patch(
            "odoo.addons.base_external_system_http.models.external_system_adapter_http.requests.get",
            return_value=_FakeResponse(status_code=200, text="ok"),
        ):
            # Success is signaled by base adapter raising UserError.
            with self.assertRaises(UserError):
                self.record.action_test_connection()

    def test_strip_empty_data(self):
        """Strip data from structure."""
        data = {"bla": "  ", "more_bla": []}
        stripped_data = self.record.interface.strip_empty_data(data)
        self.assertEqual(stripped_data, {"bla": ""})
