# Copyright 2017 LasLabs Inc.
# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from abc import ABC, abstractmethod
from contextlib import contextmanager

from odoo import _
from odoo.exceptions import ValidationError


class ExternalSystemAdapter(ABC):
    """This is the model that should be inherited for new external systems."""

    _name = "external.system.adapter"
    _description = "External System Adapter"

    def __init__(self, external_system):
        """Link adapterclass to specific remote system."""
        self.external_system = external_system
        self.external_system_path = None
        self.client_instance = None

    @contextmanager
    def client(self):
        """Client object usable as a context manager to include destruction.

        Yields the result from ``get_client``, then calls
        ``destroy_client`` to cleanup the client.

        Yields:
            mixed: An object representing the client connection to the remote system.
        """
        client = self.get_client()
        try:
            self.client_instance = client
            if self.external_system.remote_path:
                self._cd(self.external_system.remote_path)
            yield self
        finally:
            self.client_instance = None
            self.destroy_client()

    @abstractmethod
    def get_client(self):
        """Return a usable client representing the remote system."""
        raise NotImplementedError

    @abstractmethod
    def destroy_client(self):
        """Perform any logic necessary to destroy the client connection.

        Args: client (mixed): The client that was returned by ``get_client``.
        """
        raise NotImplementedError

    def cd(self, path):
        """Change to path on the remote system."""
        self.external_system_path = path
        self._cd(path.remote_path)

    @abstractmethod
    def _cd(self, remote_path):
        """Concrete subclasses need to implement this method."""
        raise NotImplementedError

    def test_connection(self):
        """Test connection.

        Actual test method should be overriden in implementation class. This class
        takes care of feedback to the user.
        """
        try:
            self._test_connection()
        except Exception as exc:
            raise ValidationError(_("Connection faild with error %s") % exc)

    @abstractmethod
    def _test_connection(self):
        """Adapters should override this method.

        If a connection cannot be made, an Exception should be raised, either by
        the used libraries, or manually by the implementation method.
        """
        raise NotImplementedError
