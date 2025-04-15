# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.base.models.res_users import is_reified_group


class ResUsers(models.Model):

    _inherit = "res.users"

    groups_id = fields.Many2many(
        readonly=True,
    )

    def write(self, values):
        # remove virtual group fields to make res users access rights view readonly
        values = {
            fname: value
            for fname, value in values.items()
            if not is_reified_group(fname)
        }
        return super().write(values)
