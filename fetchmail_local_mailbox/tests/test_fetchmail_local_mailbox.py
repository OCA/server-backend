# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import os.path
import shutil
import tempfile

from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase


class TestFetchmailLocalMailbox(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        mailbox_path = tempfile.mkdtemp()
        for name in ("cur", "new", "tmp"):
            os.mkdir(os.path.join(mailbox_path, name))
        shutil.copy(
            os.path.join(
                get_module_path("fetchmail_local_mailbox"),
                "examples",
                "test_fetchmail_local_mailbox",
            ),
            os.path.join(mailbox_path, "new"),
        )
        self.fetchmail_server = self.env["fetchmail.server"].create(
            {
                "name": "test server",
                "type": "local_mailbox",
                "mailbox_path": mailbox_path,
                "mailbox_type": "maildir",
            }
        )
        self.fetchmail_server.button_confirm_login()
        self.env["ir.config_parameter"].set_param(
            "mail.catchall.domain", "fetchmail_local_mailbox_test",
        )
        self.alias = self.env["mail.alias"].create(
            {
                "alias_name": "partner",
                "alias_model_id": self.env.ref("base.model_res_partner").id,
            }
        )
        self.patch(self.cr, "commit", lambda *args: None)

    def test_fetchmail(self, assert_new_partner=True):
        """Test mail processing"""
        partners = self.env["res.partner"].search([])
        self.fetchmail_server._fetch_mails()
        new_partners = self.env["res.partner"].search([]) - partners
        if assert_new_partner:
            self.assertTrue(new_partners, "No new partner created")
        # do the same thing again, now we shouldn't get a new partner
        partners = self.env["res.partner"].search([])
        self.fetchmail_server._fetch_mails()
        new_partners = self.env["res.partner"].search([]) - partners
        self.assertFalse(new_partners, "Duplicate partner created")

    def test_fetchmail_delete(self):
        """Test mail deletion"""
        self.fetchmail_server.mailbox_delete_processed = True
        self.test_fetchmail()
        self.assertFalse(
            os.listdir(os.path.join(self.fetchmail_server.mailbox_path, "cur",))
        )

    def test_fetchmail_general_failure(self):
        """Test failures in mail fetching"""
        self.fetchmail_server.mailbox_path = "/nonexisting/noncreateable"
        self.test_fetchmail(False)

    def test_fetchmail_processing_failure(self):
        """Test failures in mail processing"""
        self.alias.unlink()
        self.test_fetchmail(False)
