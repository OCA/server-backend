# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

from .helpers import filter_odoo_x2many_commands


class RolePolicyMenuActionCommon(models.AbstractModel):
    _name = "role.policy.menu.action.common"
    _description = "Role Policy - common code for ir.ui.menu and ir.actions.actions"

    @api.model_create_multi
    def create(self, vals_list):
        keep_ids = self._get_role_policy_group_keep_ids()
        for vals in vals_list:
            if not self.env.context.get("role_policy_init") and "groups_id" in vals:
                commands = filter_odoo_x2many_commands(
                    vals.get("groups_id", []), keep_ids
                )
                if commands:
                    vals["groups_id"] = commands
                else:
                    del vals["groups_id"]
            if "role_ids" in vals:
                roles = self.env["res.users.role"].browse(vals["role_ids"][0][2])
                vals.setdefault("groups_id", []).extend(
                    [(4, x.id) for x in roles.mapped("group_id")]
                )
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("role_policy_init") and "groups_id" in vals:
            # keep untouchable groups as well as role groups
            keep_ids = self._get_role_policy_group_keep_ids()
            keep_ids += self.groups_id.filtered(lambda r: r.role).ids
            commands = filter_odoo_x2many_commands(vals.get("groups_id", []), keep_ids)
            if commands:
                vals["groups_id"] = commands
            else:
                del vals["groups_id"]
        res = super().write(vals)
        if "role_ids" in vals:
            for o in self:
                group_cmds = [(4, x.id) for x in o.role_ids.mapped("group_id")]
                if group_cmds:
                    o.write({"groups_id": group_cmds})
        return res
