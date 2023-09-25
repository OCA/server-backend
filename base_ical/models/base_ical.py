# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


import datetime
from urllib.parse import urlparse, urlunparse

import pytz
import vobject
from dateutil import relativedelta

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class BaseIcal(models.Model):
    _name = "base.ical"
    _description = "Definition of an iCal export"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    model_id = fields.Many2one("ir.model", required=True, ondelete="cascade")
    model = fields.Char(related="model_id.model")
    domain = fields.Char(
        required=True, default="[]", help="You can use variables `env` and `user` here"
    )
    preview = fields.Text(compute="_compute_preview")
    expression_dtstamp = fields.Char(
        required=True,
        vevent_field="dtstamp",
        string="DTSTAMP",
        help="You can use variables `record` and `user` here",
        default="record.write_date",
    )
    expression_uid = fields.Char(
        required=True,
        vevent_field="uid",
        string="UID",
        help="You can use variables `record` and `user` here",
    )
    expression_dtstart = fields.Char(
        required=True,
        vevent_field="dtstart",
        string="DTSTART",
        help="You can use variables `record` and `user` here",
    )
    expression_dtend = fields.Char(
        required=True,
        vevent_field="dtend",
        string="DTEND",
        help="You can use variables `record` and `user` here",
    )
    expression_summary = fields.Char(
        required=True,
        vevent_field="summary",
        string="SUMMARY",
        help="You can use variables `record` and `user` here",
        default="record.display_name",
    )
    user_url = fields.Char(compute="_compute_user_fields", string="URL")
    user_active = fields.Boolean(compute="_compute_user_fields")
    auto = fields.Boolean(
        "Enable automatically",
        help="If you check this, the calendar will be enabled for all current and "
        "future users. Not that unchecking this will not disable existing calendar "
        "subscriptions",
    )

    def _valid_field_parameter(self, field, name):
        return super()._valid_field_parameter(field, name) or name == "vevent_field"

    @api.depends(
        "model_id",
        "domain",
        "expression_dtstamp",
        "expression_uid",
        "expression_dtstart",
        "expression_dtend",
        "expression_summary",
    )
    def _compute_preview(self):
        for this in self:
            this.preview = this._get_ical()

    def _compute_user_fields(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for this in self:
            token = this._get_user_tokens()[:1]
            vals = {"user_url": False, "user_active": False}
            if token:
                vals.update(
                    user_url=urlunparse(
                        urlparse(base_url)._replace(path="/base_ical/%s" % token.token)
                    ),
                    user_active=token.active,
                )
            this.update(vals)

    @api.onchange("model_id")
    def _onchange_model_id(self):
        for field_name, field in self._fields.items():
            if hasattr(field, "vevent_field"):
                self[field_name] = False
        self.update(
            self.default_get(["domain", "expression_dtstamp", "expression_summary"])
        )
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        self.expression_uid = "'%%s-%s@%s' %% record.id" % (
            self.env.cr.dbname,
            urlparse(base_url).hostname,
        )

    @api.constrains(
        "domain",
        "expression_dtstamp",
        "expression_uid",
        "expression_dtstart",
        "expression_dtend",
        "expression_summary",
    )
    def _check_domain(self):
        for this in self:
            this._get_ical()

    @api.model_create_multi
    def create(self, vals_list):
        """Enable calendar for all users if auto flag is checked"""
        result = super().create(vals_list)
        result.filtered("auto")._enable_all_users()
        return result

    def write(self, vals):
        """Enable calendar for all users if auto flag is checked"""
        result = super().write(vals)
        if vals.get("auto"):
            self._enable_all_users()
        return result

    def _get_user_tokens(self):
        return (
            self.env["base.ical.token"]
            .with_context(active_test=False)
            .search(
                [
                    ("user_id", "=", self.env.user.id),
                    ("ical_id", "in", self.ids),
                ]
            )
        )

    def _get_eval_expression_context(self, record):
        """Return the evaluation context for expression evaluation"""
        return {
            "record": record,
            "user": self.env.user,
            "timedelta": datetime.timedelta,
            "relativedelta": relativedelta.relativedelta,
        }

    def _get_eval_domain_context(self):
        """Return the evaluation context for domain evaluation"""
        return {
            "user": self.env.user,
            "env": self.env,
        }

    def _get_events(self):
        """Return events based on model_id and domain"""
        self.ensure_one()
        return self.env[self.model_id.sudo().model].search(
            safe_eval(self.domain, self._get_eval_domain_context())
        )

    def _get_ical(self):
        """Return the vcalendar as text"""
        if not all(
            self[field_name]
            for field_name, field in self._fields.items()
            if hasattr(field, "vevent_field") and field.required
        ):
            return False
        calendar = vobject.iCalendar()
        for record in self._get_events():
            event = calendar.add("vevent")
            for field_name, field in self._fields.items():
                if not hasattr(field, "vevent_field"):
                    continue
                value = safe_eval(
                    self[field_name], self._get_eval_expression_context(record)
                )
                event.add(field.vevent_field).value = self._format_ical_value(
                    field, value
                )
        return calendar.serialize()

    def _format_ical_value(self, field, value):
        """Add timezone to datetime values"""
        if isinstance(value, datetime.datetime):
            return pytz.utc.localize(value).astimezone(pytz.timezone(self.env.user.tz))
        return value

    def _enable_all_users(self, users=None):
        """Enable calendar for all users"""
        for this in self:
            for user in users or self.env["res.users"].search(
                [("groups_id", "=", self.env.ref("base.group_user").id)]
            ):
                this.with_user(user).action_enable()

    def action_enable(self):
        """Create or activate current user's token"""
        token = self._get_user_tokens()[:1]
        if token and not token.active:
            token.active = True
        elif not token:
            self.env["base.ical.token"].create(
                {"ical_id": self.id, "user_id": self.env.user.id}
            )

    def action_disable(self):
        """Deactivate current user's token"""
        token = self._get_user_tokens()[:1]
        if token and token.active:
            token.active = False
