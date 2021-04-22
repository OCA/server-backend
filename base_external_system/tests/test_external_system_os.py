# Copyright 2017 LasLabs Inc.
# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import tempfile

from odoo.tests.common import TransactionCase


class TestExternalSystemOs(TransactionCase):
    def test_context_manager(self):
        """Check context-manager for client."""
        working_dir = os.getcwd()
        system = self.env.ref("base_external_system.external_system_os")
        with system.client() as client:
            self.assertEqual(client.client_instance, os)
            self.assertEqual(client.client_instance.getcwd(), system.remote_path)
        self.assertEqual(os.getcwd(), working_dir)

    def test_path_context_manager(self):
        """Check context-manager for external_system_path."""
        working_dir = os.getcwd()
        sink_path = self.env.ref("base_external_system.external_system_sink_path")
        source_path = self.env.ref("base_external_system.external_system_source_path")
        # Nesting three context managers to get temporary directories and
        # of course the remote system instance.
        with tempfile.TemporaryDirectory() as tmpsinkdirname:
            sink_path.remote_path = tmpsinkdirname
            with tempfile.TemporaryDirectory() as tmpsourcedirname:
                source_path.remote_path = tmpsourcedirname
                with sink_path.client() as client:
                    self.assertEqual(client.client_instance, os)
                    self.assertEqual(
                        client.client_instance.getcwd(), sink_path.remote_path
                    )
                    client.cd(source_path)
                    self.assertEqual(
                        client.client_instance.getcwd(), source_path.remote_path
                    )
        self.assertEqual(os.getcwd(), working_dir)
