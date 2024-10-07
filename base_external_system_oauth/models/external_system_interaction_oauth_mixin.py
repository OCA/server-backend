# Copyright 2023-2024 Therp BV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Use this for json request communication with token authorization."""

from odoo import _, models
from odoo.exceptions import UserError


class ExternalSystemInteractionOauthMixin(models.AbstractModel):
    """This contains method to interact with http systems using oauth authentication."""

    _name = "external.system.interaction.oauth.mixin"
    _inherit = "external.system.interaction.mixin"
    _description = __doc__

    def post(self, endpoint=None, data=None, json=None, **kwargs):
        """Send post request."""
        headers = kwargs.pop("headers", {})
        self._set_headers(headers)
        return super().post(
            endpoint=endpoint, data=data, json=json, headers=headers, **kwargs
        )

    def get_json(self, endpoint=None, params=None, **kwargs):
        """Get json formatted data from remote system."""
        headers = kwargs.get("headers", {})
        self._set_headers(headers)
        return super().get(
            endpoint=endpoint, params=params, **dict(kwargs, headers=headers)
        )

    def _set_headers(self, headers):
        """Set headers in keyword arguments."""
        headers["Content-Type"] = "application/json"
        self._add_authorization_header(headers)

    def _add_authorization_header(self, headers):
        """Add authorization header to the passed headers dictionary."""
        token = self._get_token()
        if not token:
            raise UserError(
                _("Not able to get bearer token for system %s.") % self.name
            )
        headers["Authorization"] = "Bearer %(token)s" % {"token": token}

    def _get_token(self):
        """Need to override this with concrete implementation."""
        raise UserError(_("Methode _get_token needs concrete implementation"))
