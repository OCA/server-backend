# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.user.company_id
    )
    active_role = fields.Boolean(string="Active Role", default=True)

    @api.constrains("user_id", "company_id")
    def _check_company(self):
        for record in self:
            if (
                record.company_id
                and record.company_id != record.user_id.company_id
                and record.company_id not in record.user_id.company_ids
            ):
                raise ValidationError(
                    _('User "{}" does not have access to the company "{}"').format(
                        record.user_id.name, record.company_id.name
                    )
                )


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_enabled_roles(self):
        return self.role_line_ids.filtered(lambda rec: rec.active_role)
