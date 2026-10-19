# Copyright 2026 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

HTTP_ADAPTER = "external.system.adapter.http"


class ExternalSystem(models.Model):
    """Extend base external system"""

    _inherit = "external.system"

    endpoint_ids = fields.One2many(
        comodel_name="external.system.endpoint",
        inverse_name="system_id",
        string="Endpoints",
        help="Endpoints on remote system",
    )

    def external_test_connection(self):
        """Test connection in the UI by doing a GET on the base URL."""
        self.ensure_one()
        if self.system_type == HTTP_ADAPTER:
            with self.client() as client:
                client.get()  # Raises ValidationError on failure.
        return super().action_test_connection()
