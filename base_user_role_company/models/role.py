# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    allowed_company_ids = fields.Many2many(related="user_id.company_ids")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        domain="[('id', 'in', allowed_company_ids)]",
        help="If set, this role only applies when this is the main company selected."
        " Otherwise it applies to all companies.",
    )

    @api.constrains("user_id", "company_id")
    def _check_company(self):
        for record in self:
            if (
                record.company_id
                and record.company_id != record.user_id.company_id
                and record.company_id not in record.user_id.company_ids
            ):
                raise ValidationError(
                    _(
                        'User "%(user)s" does not have access to the company "%(company)s"'
                    )
                    % {"user": record.user_id.name, "company": record.company_id.name}
                )

    _sql_constraints = [
        (
            "user_role_uniq",
            "unique (user_id,role_id,company_id)",
            "Roles can be assigned to a user only once at a time",
        )
    ]
