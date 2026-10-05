# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import uuid

from odoo import api, fields, models

from . import dav_identity

# Fields whose modification has to reach the device. Kept in sync with
# dav_server.ical. Logging every write would make sync-tokens useless, because
# Odoo bumps ``write_date`` for reasons unrelated to the calendar.
EVENT_MAPPED_FIELDS = {
    "name",
    "description",
    "notes",
    "location",
    "start",
    "stop",
    "allday",
    "event_tz",
    "user_id",
    "partner_ids",
    "recurrency",
    "rrule",
    "rrule_type",
    "rrule_type_ui",
    "end_type",
    "interval",
    "count",
    "until",
    "weekday",
    "byday",
    "month_by",
    "day",
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
    "privacy",
    "show_as",
    "alarm_ids",
}


class DavCalendarEvent(models.Model):
    # Not named ``CalendarEvent``: reusing a core class name makes the ORM
    # confusing about which class owns the model. See models/dav_identity.py
    # for why this model declares its own ``dav_uid`` instead of using a mixin.
    _inherit = ["calendar.event"]

    dav_uid = fields.Char(
        string="DAV UID",
        index=True,
        copy=False,
        readonly=True,
        default=lambda self: uuid.uuid4().hex,
        help="Stable identifier used as the DAV UID and as the resource href.",
    )

    def _dav_mapped_fields(self):
        return EVENT_MAPPED_FIELDS

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        dav_identity.log_changes(records, "create")
        return records

    def write(self, vals):
        relevant = bool(set(vals) & self._dav_mapped_fields())
        result = super().write(vals)
        if relevant:
            dav_identity.log_changes(self, "write")
        return result

    def unlink(self):
        # Logged before the rows disappear: the change log has to record which
        # records vanished so clients drop them on their next sync.
        dav_identity.log_changes(self, "unlink")
        return super().unlink()