# Copyright 2021 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).


from odoo import fields, models


class GroupGroupsIntoRole(models.TransientModel):
    """
    This wizard is used to group different groups into a role.
    """

    _name = "group.groups.into.role"
    _description = "Group groups into a role"
    name = fields.Char(
        required=True,
        help="Group groups into a role and specify a name for this role",
    )

    def create_role(self):
        selected_group_ids = self.env.context.get("selected_group_ids", [])
        vals = {
            "name": self.name,
            "implied_ids": selected_group_ids,
        }
        self.env["res.users.role"].create(vals)
