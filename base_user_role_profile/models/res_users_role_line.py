# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    profile_id = fields.Many2one(related="role_id.profile_id")
