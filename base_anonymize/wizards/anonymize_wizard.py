# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class AnonymizeWizard(models.TransientModel):
    _name = "anonymize.wizard"
    _description = "Anonymization wizard"

    def action_run(self):
        self.check_access("create")
        self.env["anonymize.field"]._run_all()
