# Copyright 2023 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Extend base adapter model for connections through http(s)."""
from odoo import api, models

from ..tools import initialize_request_logging

initialize_request_logging()


class ExternalSystemAdapterHTTP(models.AbstractModel):
    """HTTP external system Adapter"""

    _name = "external.system.adapter.http"
    _inherit = ["external.system.adapter", "external.system.interaction.mixin"]
    _description = __doc__

    @api.model
    def external_get_client(self):
        """Return self as the client."""
        return self

    @api.model
    def external_destroy_client(self, client):
        """If needed logout of server."""
