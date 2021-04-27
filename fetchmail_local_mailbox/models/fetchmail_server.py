# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import mailbox

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    type = fields.Selection(selection_add=[("local_mailbox", "Local mailbox")])
    mailbox_type = fields.Selection([("maildir", "Maildir")], default="maildir")
    mailbox_path = fields.Char()
    mailbox_delete_processed = fields.Boolean("Delete processed mails from mailbox")

    @api.multi
    def connect(self):
        self.ensure_one()
        if self.type == "local_mailbox":
            mailbox_type2class = {
                "maildir": mailbox.Maildir,
            }
            return mailbox_type2class[self.mailbox_type](self.mailbox_path)
        return super().connect()

    @api.model
    def _fetch_mails(self):
        return (
            self.search(
                [("state", "=", "done"), ("type", "=", "local_mailbox")]
            ).fetch_mail()
            and super()._fetch_mails()
        )

    @api.multi
    def fetch_mail(self):
        for this in self:
            if this.type != "local_mailbox":
                continue
            _logger.info("start checking for new emails in %s", this.mailbox_path)
            extra_context = {
                "fetchmail_cron_running": True,
                "fetchmail_server_id": this.id,
                "server_type": this.type,
            }
            processing_func = getattr(
                this.with_context(**extra_context),
                "_process_mail_%s" % this.mailbox_type,
            )
            try:
                count = failed = 0
                mail_box = this.connect()
                mail_box.lock()
                for key, message in mail_box.items():
                    try:
                        processing_func(mail_box, key, message)
                    except Exception:
                        failed += 1
                        _logger.info(
                            "Failed to process mail %s from %s.",
                            key,
                            this.mailbox_path,
                            exc_info=True,
                        )
                    count += 1
                    # pylint: disable=invalid-commit
                    self.env.cr.commit()
                mail_box.close()
                _logger.info(
                    "Fetched %d email(s) from %s; %d succeeded, %d failed.",
                    count,
                    this.mailbox_path,
                    (count - failed),
                    failed,
                )
            except Exception:
                _logger.info(
                    "General failure when trying to fetch mail from %s.",
                    this.mailbox_path,
                    exc_info=True,
                )
            this.write({"date": fields.Datetime.now()})
        return super(
            FetchmailServer, self.filtered(lambda x: x.type != "local_mailbox"),
        ).fetch_mail()

    @api.multi
    def _process_mail_maildir(self, mail_box, key, message):
        """Process a mail from a maildir mailbox"""
        if not self.mailbox_delete_processed and "S" in message.get_flags():
            return
        if message.get_subdir() == "new":
            message.set_subdir("cur")
        result = self.env["mail.thread"].message_process(
            self.object_id.model,
            message.as_string(),
            save_original=self.original,
            strip_attachments=(not self.attach),
        )
        message.add_flag("S")
        mail_box[key] = message
        if self.mailbox_delete_processed:
            mail_box.discard(key)
        return result
