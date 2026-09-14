import logging

from odoo import models

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = "base"

    def unlink(self):
        if not self.env.context.get("no_record_trace"):
            try:
                self.env["record.trace"].sudo().log_unlink(self)
            except Exception as err:
                _logger.warning(f"record trace failed for {self._name} : {err}")
        return super().unlink()
