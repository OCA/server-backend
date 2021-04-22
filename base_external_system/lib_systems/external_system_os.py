# Copyright 2017 LasLabs Inc.
# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os

from .external_system_adapter import ExternalSystemAdapter


class ExternalSystemOs(ExternalSystemAdapter):
    """This is an Interface implementing the OS module.

    For the most part, this is just a sample of how to implement an external
    system interface. This is still a fully usable implementation, however.
    """

    _name = "external.system.os"
    _description = "External System OS"

    original_dir = None

    def get_client(self):
        """Return a usable client representing the remote system."""
        return os

    def destroy_client(self):
        """Perform any logic necessary to destroy the client connection.

        Args: client (mixed): The client that was returned by ``get_client``.
        """
        if self.original_dir:
            os.chdir(self.original_dir)
            self.original_dir = None

    def _cd(self, remote_path):
        """Actually change the os directory, saving original."""
        # Save previous/original dir if not done by get_client.
        if not self.original_dir:
            self.original_dir = os.getcwd()
        os.chdir(remote_path)

    def _test_connection(self):
        """Test wether we can connect to os. Feedback to user handled by super class."""
        with self.client() as my_os:
            type(my_os) == "os"
