# Copyright 2017 LasLabs Inc.
# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Mostly trivial tests to keep up coverage."""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from ..lib_systems.external_system_adapter import ExternalSystemAdapter


class MockRemoteSystem(object):
    """Pseudo remote system."""

    def __init__(self):
        """To test context manager."""
        self.remote_path = "/original"


class MockExternalSystem(object):
    """Just support remote_path attribute used in MockAdapter."""

    def __init__(self):
        self.remote_path = "/mock"


class MockAdapter(ExternalSystemAdapter):
    """Provide trivial implementation of methods to test abstract class."""

    def get_client(self):
        """Return a usable client representing the remote system."""
        server = MockRemoteSystem()
        return server

    def destroy_client(self):
        """Perform any logic necessary to destroy the client connection."""
        pass

    def _cd(self, remote_path):
        """Change path."""
        self.client_instance.remote_path = remote_path

    def _test_connection(self):
        """Adapters should override this method."""
        super()._test_connection()


class TestExternalSystemAdapter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.adapter = MockAdapter(MockExternalSystem())

    def test_context_manager(self):
        """Context manager should call get_client and later destroy_client."""
        with self.adapter.client() as client:
            self.assertTrue(isinstance(client, MockAdapter))
            self.assertTrue(isinstance(client.external_system, MockExternalSystem))
            self.assertTrue(isinstance(client.client_instance, MockRemoteSystem))
            self.assertEqual(client.client_instance.remote_path, "/mock")

    def test_test_connection(self):
        """It should raise a ValidationError."""
        with self.assertRaises(ValidationError):
            self.adapter.test_connection()
