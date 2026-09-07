import datetime
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    def write(self, vals):
        res = super().write(vals)

        if "date_to" in vals:
            self.mapped("user_id").activity_update_role_reminder()
            return

        return res

    def unlink(self):
        users = self.mapped("user_id")
        res = super().unlink()
        users.activity_update_role_reminder()
        return res

    @api.model
    def cron_role_reminder(self):
        _logger.info("Trigger role expiration reminders")
        users = self.search(self._get_reminder_days_domain()).mapped("user_id")
        users = users.filtered(
            lambda user: not user.partner_id.activity_search(
                ["base_user_role_activity.mail_activity_role_expire"]
            )
        )
        users.activity_update_role_reminder()

    @api.model
    def _get_reminder_days_domain(self):
        reminder_days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_user_role_activity.reminder_days", 30)
        )
        domain = [
            ("is_enabled", "=", True),
            (
                "date_to",
                "<=",
                fields.Date.today() + datetime.timedelta(days=reminder_days),
            ),
            "|",
            ("date_from", "=", False),
            ("date_from", "<", fields.Date.today()),  # ignore short term roles
        ]
        return domain
