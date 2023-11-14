# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class ResUsersEffectivePermission(models.TransientModel):
    _name = "res.users.effective.permission"
    _order = "model_human_name"
    _description = "Effective permissions"

    model_id = fields.Many2one("ir.model", string="Model")
    model_name = fields.Char(related="model_id.model", string="Model name")
    model_human_name = fields.Char(
        related="model_id.name", store=True, string="Human readable model name"
    )
    create_permission = fields.Boolean("Create")
    create_domain = fields.Char("Create restrictions")
    create_domain_widget = fields.Char(related="create_domain", string="Create domain")
    read_permission = fields.Boolean("Read")
    read_domain = fields.Char("Read restrictions")
    read_domain_widget = fields.Char(related="read_domain", string="Read domain")
    write_permission = fields.Boolean("Write")
    write_domain = fields.Char("Write restrictions")
    write_domain_widget = fields.Char(related="write_domain", string="Write domain")
    unlink_permission = fields.Boolean("Delete")
    unlink_domain = fields.Char("Delete restrictions")
    unlink_domain_widget = fields.Char(related="unlink_domain", string="Delete domain")

    def _generate_permissions(self, user):
        permissions = self.browse([])
        operations = ("create", "unlink", "read", "write")
        IrRule = (
            self.env["ir.rule"]
            .with_user(user)
            .with_company(user.company_id)
            .with_context(
                allowed_company_ids=user.company_id.ids,
            )
        )
        for model_record in self.env["ir.model"].search([]):
            if model_record.model not in self.env:
                continue
            model = (
                self.env[model_record.model]
                .with_user(user)
                .with_company(user.company_id)
                .with_context(allowed_company_ids=user.company_id.ids)
            )
            vals = {"model_id": model_record.id}
            vals.update(
                {
                    "%s_permission"
                    % operation: model.check_access_rights(operation, False)
                    for operation in operations
                }
            )
            vals.update(
                {
                    "%s_domain"
                    % operation: IrRule._compute_domain(model._name, operation)
                    for operation in operations
                }
            )
            permissions += self.create(vals)
        return permissions
