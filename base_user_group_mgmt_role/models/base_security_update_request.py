# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class BaseSecurityUpdateRequest(models.Model):

    _inherit = "base.security.update.request"

    def action_second_approval(self):
        res = super().action_second_approval()
        self.env["res.users.role"].sudo().cron_update_users()
        return res
