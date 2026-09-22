from odoo import api, models


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    def write(self, vals):
        history_lines = []
        for line in self:
            history_line = {
                "performed_action": "edit",
                "user_id": line.user_id.id,
                "old_role_id": line.role_id.id,
                "old_date_from": line.date_from,
                "old_date_to": line.date_to,
                "old_is_enabled": line.is_enabled,
                "new_role_id": vals.get("role_id", line.role_id.id),
                "new_date_from": vals.get("date_from", line.date_from),
                "new_date_to": vals.get("date_to", line.date_to),
                "new_is_enabled": vals.get("is_enabled", line.is_enabled),
            }
            if (
                history_line["old_role_id"] == history_line["new_role_id"]
                and history_line["old_date_from"] == history_line["new_date_from"]
                and history_line["old_date_to"] == history_line["new_date_to"]
                and history_line["old_is_enabled"] == history_line["new_is_enabled"]
            ):
                continue

            history_lines.append(history_line)

        res = super().write(vals)
        self.env["base.user.role.line.history"].sudo().create(history_lines)

        return res

    @api.model_create_multi
    def create(self, vals_list):
        history_lines = []
        for line in vals_list:
            history_line = {
                "performed_action": "add",
                "user_id": line.get("user_id", False),
                "new_role_id": line.get("role_id", False),
                "new_date_from": line.get("date_from", False),
                "new_date_to": line.get("date_to", False),
                "new_is_enabled": line.get("is_enabled", True),
            }
            history_lines.append(history_line)

        res = super().create(vals_list)
        self.env["base.user.role.line.history"].sudo().create(history_lines)

        return res

    def unlink(self):
        history_lines = []
        for line in self:
            history_line = {
                "performed_action": "unlink",
                "user_id": line.user_id.id,
                "old_role_id": line.role_id.id,
                "old_date_from": line.date_from,
                "old_date_to": line.date_to,
                "old_is_enabled": line.is_enabled,
            }
            history_lines.append(history_line)

        res = super().unlink()
        self.env["base.user.role.line.history"].sudo().create(history_lines)

        return res
