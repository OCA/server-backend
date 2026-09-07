from markupsafe import Markup

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def activity_update_role_reminder(self):
        activity_type_xmlid = "base_user_role_activity.mail_activity_role_expire"
        for user in self:
            expiring_lines = user.role_line_ids.filtered_domain(
                self.env["res.users.role.line"]._get_reminder_days_domain()
            )
            existing_active_activities = user.partner_id.activity_search(
                [activity_type_xmlid]
            )
            if not expiring_lines:
                if existing_active_activities:
                    # cleanup outdated activities
                    existing_active_activities.unlink()
                continue

            min_deadline = min(expiring_lines.mapped("date_to"))
            if existing_active_activities:
                existing_active_activity = existing_active_activities[0]
                if existing_active_activity.date_deadline == min_deadline:
                    continue  # No update needed
                # something changed, remove existing activity and recreate
                existing_active_activities.unlink()

            existing_activities = user.partner_id.with_context(
                active_test=False
            ).activity_search(
                [activity_type_xmlid],
                additional_domain=[("date_deadline", ">=", min_deadline)],
            )
            if existing_activities:
                continue  # An activity with the correct deadline already processed

            activity_type_id = self.env["ir.model.data"]._xmlid_to_res_id(
                activity_type_xmlid, raise_if_not_found=False
            )
            activity_type = self.env["mail.activity.type"].browse(activity_type_id)

            # receive manager independet of selected company
            employees = (
                self.env["hr.employee"]
                .sudo()
                .search([("user_id", "=", user.id), ("parent_id", "!=", False)])
            )
            manager = employees.filtered(
                lambda e: e.company_id == self.env.company
            ).parent_id
            if not manager and employees:
                manager = employees[0].parent_id

            user.partner_id.activity_schedule(
                activity_type_id=activity_type_id,
                date_deadline=min(expiring_lines.mapped("date_to")),
                note=activity_type.default_note
                % {
                    "user": user._get_html_link(),
                    "roles": Markup(
                        "<br/> -".join(
                            [
                                f"{line.role_id.name} ({line.date_to})"
                                for line in expiring_lines
                            ]
                        )
                    ),
                },
                user_id=manager.user_id.id or user.id,
            )
