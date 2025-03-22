# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AnonymizeWizard(models.TransientModel):
    _name = "anonymize.wizard"
    _description = "Anonymization wizard"

    def action_run(self):
        self.check_access_rights("create")
        self.check_access_rights("write")
        for field in self.env["anonymize.field"].search([("applicable", "=", True)]):
            self.env[field.method]._run(field)

        # needed to wipe deleted attachments
        self.env["ir.attachment"]._gc_file_store()
