# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging
import secrets

from odoo import models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

PARAM = "base_anonymize.password"


class AnonymizeMethodRandomPassword(models.AbstractModel):
    _inherit = "anonymize.method"
    _name = "anonymize.method.random.password"
    _description = "Random password, the same for all users"

    def _run(self, field):
        """One random password per run, hashed as Odoo does. The clear text goes
        to the system parameter base_anonymize.password, readable by whoever
        receives the anonymized database."""
        password = secrets.token_urlsafe(12)
        hashed = self.env["res.users"]._crypt_context().hash(password)
        # res.users.password is computed and not stored for the ORM, the column
        # is created by res.users.init()
        count = self._update(
            field, SQL("%s", hashed), skip_null=False, check_stored=False
        )
        self.env["ir.config_parameter"].sudo().set_param(PARAM, password)
        _logger.info("Passwords reset, see system parameter %s", PARAM)
        return count
