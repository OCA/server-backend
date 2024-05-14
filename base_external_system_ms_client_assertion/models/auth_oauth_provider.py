# Copyright 2024 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=no-self-use
"""Provide extra functionality to use Microsoft oauth for applications."""

from odoo import fields, models


class AuthOAuthProvider(models.Model):
    """Abstract model to communicate with oauth authentication provider."""

    _inherit = "auth.oauth.provider"

    provider_type = fields.Selection(
        selection_add=[
            ("microsoft_client_assertion", "Microsoft Client Assertion"),
        ],
    )

    def _get_access_token_microsoft_client_assertion(self):
        """Overrule standard method to do nothing."""
        return None
