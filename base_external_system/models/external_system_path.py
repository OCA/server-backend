# Copyright 2020 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""Provide multiple path's on external system.

Path's might be directories in filesystems, or folders on ftp servers, or endpoints
for http rest calls. Anything where on one system, there might be multiple resources
that can be identified by a path.
"""
from contextlib import contextmanager

from odoo import fields, models


class ExternalSystemPath(models.Model):

    _name = "external.system.path"
    _description = "External System Path"

    system_id = fields.Many2one(comodel_name="external.system", required=True)
    name = fields.Char(
        required=True, help="This is the canonical (humanized) name for the system.",
    )
    remote_path = fields.Char(
        required=True,
        help="Restrict to this directory path on the remote, if applicable.",
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(system_id, name)", "Name must be unique for system."),
        (
            "path_uniq",
            "UNIQUE(system_id, remote_path)",
            "Path must be unique for system.",
        ),
    ]

    @contextmanager
    def client(self):
        """Connect to remote client and immediately set path.

        This is basically just a shortcut for connecting to a client and
        immediately changing the path.
        """
        self.ensure_one()
        with self.system_id.client() as client:
            client.cd(self)
            yield client
