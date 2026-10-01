from odoo import api, models


class ResUsersRoleLine(models.Model):
    _inherit = "res.users.role.line"

    @api.model
    def _prepare_role_line_history_lines_write(self, role_line, role_line_vals):
        return {
            "performed_action": "edit",
            "user_id": role_line.user_id.id,
            "old_role_id": role_line.role_id.id,
            "old_date_from": role_line.date_from,
            "old_date_to": role_line.date_to,
            "old_is_enabled": role_line.is_enabled,
            "new_role_id": role_line_vals.get("role_id", role_line.role_id.id),
            "new_date_from": role_line_vals.get("date_from", role_line.date_from),
            "new_date_to": role_line_vals.get("date_to", role_line.date_to),
            "new_is_enabled": role_line_vals.get("is_enabled", role_line.is_enabled),
        }

    def write(self, vals):
        history_lines = []
        for line in self:
            history_line = self._prepare_role_line_history_lines_write(line, vals)
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

    @api.model
    def _prepare_role_line_history_lines_create(self, role_line_vals):
        return {
            "performed_action": "add",
            "user_id": role_line_vals.get("user_id", False),
            "new_role_id": role_line_vals.get("role_id", False),
            "new_date_from": role_line_vals.get("date_from", False),
            "new_date_to": role_line_vals.get("date_to", False),
            "new_is_enabled": role_line_vals.get("is_enabled", True),
        }

    @api.model_create_multi
    def create(self, vals_list):
        history_lines = []
        for line in vals_list:
            history_line = self._prepare_role_line_history_lines_create(line)
            history_lines.append(history_line)
        res = super().create(vals_list)
        self.env["base.user.role.line.history"].sudo().create(history_lines)
        return res

    @api.model
    def _prepare_role_line_history_lines_unlink(self, role_line):
        return {
            "performed_action": "unlink",
            "user_id": role_line.user_id.id,
            "old_role_id": role_line.role_id.id,
            "old_date_from": role_line.date_from,
            "old_date_to": role_line.date_to,
            "old_is_enabled": role_line.is_enabled,
        }

    def unlink(self):
        history_lines = []
        for line in self:
            history_line = self._prepare_role_line_history_lines_unlink(line)
            history_lines.append(history_line)
        res = super().unlink()
        self.env["base.user.role.line.history"].sudo().create(history_lines)
        return res
