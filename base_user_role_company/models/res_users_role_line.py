# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    allowed_company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Allowed Companies",
        related="user_id.company_ids",
    )
    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companies",
        domain="[('id', 'in', allowed_company_ids)]",
        help="If set, this role only applies when the main company selected is"
        " one of these. Otherwise it applies to all companies.",
    )

    @api.constrains("user_id", "company_ids")
    def _check_company(self):
        for record in self:
            allowed_companies = record.user_id.company_ids | record.user_id.company_id
            invalid_companies = record.company_ids - allowed_companies
            if invalid_companies:
                raise ValidationError(
                    self.env._(
                        'User "%(user)s" does not have access to: %(companies)s',
                        user=record.user_id.name,
                        companies=", ".join(invalid_companies.mapped("name")),
                    )
                )
