from odoo import fields, models


class RoleAddUsersWizard(models.TransientModel):
    _name = "role.add.users.wizard"
    _description = "Wizard to add multiple users to a role"

    role_id = fields.Many2one(
        comodel_name="res.users.role",
        required=True,
        ondelete="cascade",
    )
    user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Users",
        required=True,
    )
    date_from = fields.Date("From")
    date_to = fields.Date("To")

    def action_add_users(self):
        existing_users = self.role_id.line_ids.user_id
        new_users = self.user_ids - existing_users
        self.env["res.users.role.line"].create(
            [
                {
                    "role_id": self.role_id.id,
                    "user_id": user.id,
                    "date_from": self.date_from,
                    "date_to": self.date_to,
                }
                for user in new_users
            ]
        )
        return {"type": "ir.actions.act_window_close"}
