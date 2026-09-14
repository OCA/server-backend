import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Excluded models : technical / heavy (avoid recursion)
EXCLUDED_MODELS = {
    "record.trace",
    "ir.logging",
    "ir.model.data",
    "ir.model.fields",
    "ir.property",
    "ir.attachment",
    "ir.cron",
    "res.users.log",
    "mail.message",
    "mail.followers",
    "mail.tracking.value",
    "base.import.import",
}


class RecordTrace(models.Model):
    _name = "record.trace"
    _description = "Record Deletion Trace"
    _order = "id desc"

    model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True)
    name = fields.Char()
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)

    _sql_constraints = [
        (
            "model_res_id_uniq",
            "unique(model, res_id)",
            "One trace max per deleted record.",
        ),
    ]

    @api.model
    def _is_tracked_model(self, model):
        """A model is traced only if its ir.model.track_deletions is set."""
        if model in EXCLUDED_MODELS:
            return False
        ir_model = self.env["ir.model"].search([("model", "=", model)], limit=1)
        return bool(ir_model and ir_model.track_deletions)

    @api.model
    def log_unlink(self, records):
        """Store one trace per deleted record (idempotent, best effort)."""
        model = records._name
        if not self._is_tracked_model(model) or self.env.context.get("no_record_trace"):
            return
        try:
            names = {
                rec.id: rec.display_name
                for rec in records.with_context(active_test=False)
            }
        except Exception:
            names = {}
        vals_list = [
            {
                "model": model,
                "res_id": rec.id,
                "name": names.get(rec.id),
                "user_id": self.env.uid,
            }
            for rec in records
        ]
        # ondelete records may be gone from cache : create in SQL-less mode
        self.sudo().create(vals_list)

    def _cron_purge(self):
        """Purge traces older than the retention configured via ir.config_parameter."""
        days = self.get_retention_days()
        cutoff = fields.Datetime.now() - timedelta(days=days)
        old = self.search([("create_date", "<", cutoff)])
        count = len(old)
        if count:
            old.unlink()
        _logger.info("record_trace purge : %s rows removed (cutoff %s)", count, cutoff)
        return count

    @api.model
    def get_retention_days(self):
        """Common retention (in days) for all companies, from ir.config_parameter."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("record_trace_retention_days", default=100)
        )
        try:
            return int(param)
        except (TypeError, ValueError):
            return 100
