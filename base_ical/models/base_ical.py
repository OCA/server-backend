# Copyright 2023 Hunki Enterprises BV
# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import datetime
import logging
from urllib.parse import urlparse

import pytz
import vobject
from dateutil import relativedelta

from odoo import _, api, fields, models
from odoo.tools import html2plaintext
from odoo.tools.safe_eval import safe_eval, wrap_module

_logger = logging.getLogger(__name__)

vobject_wrapped = wrap_module(__import__("vobject"), ["iCalendar", "readOne"])


class BaseIcal(models.Model):
    _name = "base.ical"
    _description = "Definition of an iCal export"

    def _get_operating_modes(self):
        return [
            ("simple", _("Simple")),
            ("advanced", _("Advanced")),
        ]

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    mode = fields.Selection("_get_operating_modes", required=True, default="simple")
    model_id = fields.Many2one("ir.model", required=True, ondelete="cascade")
    model = fields.Char("Model Name", related="model_id.model")
    domain = fields.Char(
        required=True, default="[]", help="You can use variables `env` and `user` here"
    )
    preview = fields.Text(compute="_compute_preview")
    code = fields.Text()
    expression_dtstamp = fields.Char(
        vevent_field="dtstamp",
        string="DTSTAMP",
        help="You can use variables `record` and `user` here",
        default="record.write_date",
    )
    expression_uid = fields.Char(
        vevent_field="uid",
        string="UID",
        help="You can use variables `record` and `user` here",
    )
    expression_dtstart = fields.Char(
        vevent_field="dtstart",
        string="DTSTART",
        help="You can use variables `record` and `user` here",
    )
    expression_dtend = fields.Char(
        vevent_field="dtend",
        string="DTEND",
        help="You can use variables `record` and `user` here",
    )
    expression_summary = fields.Char(
        vevent_field="summary",
        string="SUMMARY",
        help="You can use variables `record` and `user` here",
        default="record.display_name",
    )
    allowed_users_ids = fields.Many2many("res.users")
    auto = fields.Boolean(
        "Allow automatically",
        copy=False,
        help="If you check this, the calendar will be enabled for all current and "
        "future users. Not that unchecking this will not disable existing calendar "
        "subscriptions",
    )
    help_text = fields.Html(compute="_compute_help")

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
        "code",
        "mode",
    )
    def _compute_preview(self):
        for this in self:
            this.preview = this._get_ical(limit=5)

    @api.depends("mode")
    def _compute_help(self):
        for this in self:
            variables = this.default_variables()
            lines = []
            for var, desc in sorted(variables.items()):
                var = (f"<code>{v.strip()}</code>" for v in var.split(","))
                lines.append(f"<li>{', '.join(sorted(var))}: {desc}</li>")

            this.help_text = "<ul>" + "\n".join(lines) + "</ul>"

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
        "code",
        "mode",
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

    def default_variables(self):
        self.ensure_one()
        variables = {
            "datetime, relativedelta, time, timedelta": "useful Python libraries",
            "record": "Record to export",
            "user": "Current user record",
        }
        if self.mode == "advanced":
            variables.update(
                {
                    "calendar": "Output: Calendar e.g. from `_get_ics_file`",
                    "dict2ical": "Function to add the key-values of dict to ical component",
                    "event": "Output: Dictionary of an VEVENT",
                    "todo": "Output: Dictionary of an VTODO",
                    "vobject": "vobject python library",
                    "html2plaintext": "Converts HTML to plain text",
                }
            )
        return variables

    def _get_eval_expression_context(self):
        """Return the evaluation context for expression evaluation"""
        return {
            "datetime": datetime.datetime,
            "date": datetime.date,
            "relativedelta": relativedelta.relativedelta,
            "timedelta": datetime.timedelta,
            "user": self.env.user,
        }

    def _get_eval_domain_context(self):
        """Return the evaluation context for domain evaluation"""
        return {
            "user": self.env.user,
            "env": self.env,
        }

    def _get_items(self, limit=None):
        """Return events based on model_id and domain"""
        self.ensure_one()
        return self.env[self.model_id.sudo().model].search(
            safe_eval(self.domain, self._get_eval_domain_context()),
            limit=limit,
        )

    def _get_ical(self, records=None, limit=None):
        """Return the vcalendar as text"""
        if self.mode == "simple":
            return self._get_ical_simple(records=records, limit=limit)

        return self._get_ical_advanced(records=records, limit=limit)

    def _get_ical_simple(self, records=None, limit=None):
        if not all(
            self[field_name]
            for field_name, field in self._fields.items()
            if hasattr(field, "vevent_field")
        ):
            return ""

        calendar = vobject.iCalendar()
        for record in records or self._get_items(limit):
            event = calendar.add("vevent")
            for field_name, field in self._fields.items():
                if not hasattr(field, "vevent_field"):
                    continue

                if not self[field_name]:
                    continue

                ctx = self._get_eval_expression_context()
                ctx["record"] = record

                value = safe_eval(self[field_name], ctx)
                event.add(field.vevent_field).value = self._format_ical_value(
                    value, field=field
                )
        return calendar.serialize()

    def _get_ical_advanced(self, records=None, limit=None):
        if not self.code:
            return ""

        context = self._get_eval_expression_context()
        context.update(
            {
                "dict2ical": self._dict_to_ical_component,
                "html2plaintext": html2plaintext,
                "vobject": vobject_wrapped,
            }
        )

        calendar = vobject.iCalendar()
        tz = pytz.timezone(self.env.user.tz or "UTC")
        calendar.add(vobject.icalendar.TimezoneComponent(tz))
        for record in records or self._get_items(limit):
            context.update(
                {"record": record, "calendar": None, "event": None, "todo": None}
            )
            safe_eval(self.code, context, mode="exec", nocopy=True)

            cal = context.get("calendar")
            if cal:
                # Support for `_get_ics_file`
                if isinstance(cal, dict) and record.id in cal:
                    cal = cal[record.id]

                if isinstance(cal, bytes):
                    cal = cal.decode()

                if isinstance(cal, str):
                    cal = vobject.readOne(cal)

                self._copy_ical_calendar(calendar, cal)

            event, todo = map(context.get, ("event", "todo"))
            if event:
                self._dict_to_ical_component(calendar.add("vevent"), event)

            if todo:
                self._dict_to_ical_component(calendar.add("vtodo"), todo)

        return calendar.serialize()

    def _dict_to_ical_component(self, component, data):
        for key, value in data.items():
            component.add(key).value = self._format_ical_value(value)

    def _copy_ical_calendar(self, dst_calendar, src_calendar):
        for item in src_calendar.getChildren():
            if item.name.lower() in ("vevent", "vtodo"):
                dst_calendar.add(item)

    def _format_ical_value(self, value, field=None):
        """Add timezone to datetime values"""
        if isinstance(value, datetime.datetime):
            return pytz.utc.localize(value).astimezone(
                pytz.timezone(self.env.user.tz or "UTC")
            )
        return value

    def _enable_all_users(self, users=None):
        """Enable calendar for all users"""
        users = users or self.env.ref("base.group_user").users
        self.write({"allowed_users_ids": users})

    def action_new_url(self):
        """Create or activate current user's token"""

        return {
            "type": "ir.actions.act_window",
            "res_model": "base.ical.url.description",
            "name": "iCalendar URL",
            "views": [(False, "form")],
            "target": "new",
            "context": {
                "default_calendar_id": self.id,
            },
        }
