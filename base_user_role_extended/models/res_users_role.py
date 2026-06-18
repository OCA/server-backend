# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields

class ResUsersRole(models.Model):
    _inherit = "res.users.role"

    role_model_access_ids = fields.One2many(
        "role.model.access",
        "role_id",
        string="Role Model Access"
    )
