#  Copyright (c) 2024- Le Filament (https://le-filament.com)
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Add new group_user_manager to the existing signup fields
    signup_token = fields.Char(
        groups="base.group_erp_manager, group_user_management.group_user_manager",
    )
    signup_type = fields.Char(
        groups="base.group_erp_manager, group_user_management.group_user_manager",
    )
    signup_expiration = fields.Datetime(
        groups="base.group_erp_manager, group_user_management.group_user_manager",
    )
