# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Conversions between ``calendar.event`` and iCalendar.

Deliberately built on ``icalendar`` rather than the ``vobject`` dependency that
``base_dav`` uses: the wire format needs real ``VTIMEZONE`` components,
``vRecur`` round-tripping and RFC-correct VALARM triggers, none of which vobject
produces. (Odoo's own ``_get_ics_file``, used for invitation emails, encodes
VALARM triggers with a *positive* duration, which RFC 5545 reads as "after the
start" even though the field is called "Remind Before". This module emits the
spec-correct negative duration.)
"""

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from icalendar import Calendar, Component, Timezone
from icalendar.prop import vCalAddress, vText

_logger = logging.getLogger(__name__)

PRODID = "-//rossg//dav_server//EN"
UTC = timezone.utc
TZID_EXPAND_FIRST = date(1970, 1, 1)
TZID_EXPAND_LAST = date(2038, 1, 1)

# Odoo's calendar.alarm can only express "N units before", in these units only.
ALARM_UNITS = ((1440, "days"), (60, "hours"), (1, "minutes"))

RRULE_TYPES = {
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "monthly",
    "yearly": "yearly",
}

# calendar_recurrence.WEEKDAY_SELECTION
WEEKDAY_FIELDS = {
    "MO": ("mon", "MON"),
    "TU": ("tue", "TUE"),
    "WE": ("wed", "WED"),
    "TH": ("thu", "THU"),
    "FR": ("fri", "FRI"),
    "SA": ("sat", "SAT"),
    "SU": ("sun", "SUN"),
}

# iCalendar PARTSTAT -> Odoo calendar.attendee.state
PARTSTAT_TO_ODOO = {
    "NEEDS-ACTION": "needs-action",
    "ACCEPTED": "accepted",
    "TENTATIVE": "tentative",
    "DECLINED": "declined",
    "DELEGATED": "delegated",
}
ODOO_TO_PARTSTAT = {value: key for key, value in PARTSTAT_TO_ODOO.items()}

TRANSP_TO_SHOW_AS = {"OPAQUE": "busy", "TRANSPARENT": "free"}
SHOW_AS_TO_TRANSP = {"busy": "OPAQUE", "free": "TRANSPARENT"}
CLASS_TO_PRIVACY = {
    "PUBLIC": "public",
    "PRIVATE": "private",
    "CONFIDENTIAL": "confidential",
}
PRIVACY_TO_CLASS = {value: key for key, value in CLASS_TO_PRIVACY.items()}

TEXT_MAX = 100000


class UnsupportedPayload(ValueError):
    """The client sent something that cannot be represented in Odoo."""


# ======================================================================
# Export
# ======================================================================
def event_to_ical(event):
    """Serialise one master ``calendar.event`` into a VCALENDAR document."""
    calendar = Calendar()
    calendar.add("prodid", PRODID)
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    _add_timezone(calendar, event)

    # icalendar 6+ returns None from add_component(str) and leaves a bare str in
    # subcomponents, so components are built explicitly.
    component = Component()
    component.name = "VEVENT"
    calendar.add_component(component)
    component.add("uid", event.dav_uid or str(event.id))
    component.add("dtstamp", datetime.now(UTC))
    component.add("summary", event.name or "")

    if event.description:
        component.add("description", _plain_text(event.description))
    if event.location:
        component.add("location", event.location)

    _add_timing(component, event)
    _add_recurrence(component, event)
    _add_organizer(component, event)
    _add_attendees(component, event)
    _add_privacy(component, event)
    _add_alarms(component, event)

    if event.access_token:
        component.add("url", _public_url(event))
    return calendar.to_ical()


def event_timezone(event):
    """The zone an event's UTC instants should be presented in.

    ``calendar.event.event_tz`` is a pseudo-related field of the recurrence, so
    Odoo leaves it False for anything that is not a recurring series -- writing
    it directly raises ``Unable to save the recurrence with "This Event"``. The
    organiser's own timezone is what the Odoo UI falls back to, so use that.
    """
    return event.event_tz or event.user_id.tz or "UTC"


def _add_timezone(calendar, event):
    name = event_timezone(event)
    if event.allday or name == "UTC":
        return
    try:
        tzinfo = ZoneInfo(name)
        calendar.add_component(
            Timezone.from_tzinfo(
                tzinfo, first_date=TZID_EXPAND_FIRST, last_date=TZID_EXPAND_LAST
            )
        )
    except (ZoneInfoNotFoundError, ValueError):
        _logger.warning("dav_server: unknown timezone %r", name)
    except Exception:  # pragma: no cover - icalendar version drift
        _logger.debug("dav_server: VTIMEZONE expansion failed", exc_info=True)


def _add_timing(component, event):
    if event.allday:
        # DTEND is exclusive in iCalendar, and Odoo stores the same convention.
        component.add("dtstart", _as_date(event.start))
        component.add("dtend", _as_date(event.stop))
        return
    zone = event_timezone(event)
    component.add("dtstart", _with_zone(event.start, zone))
    component.add("dtend", _with_zone(event.stop, zone))


def rrule_text(raw):
    """Extract the RRULE body from ``calendar.recurrence.rrule``.

    Odoo 17 stores that column over *two* lines::

        DTSTART:20261005T102000
        RRULE:FREQ=MONTHLY;INTERVAL=2;COUNT=5;BYMONTHDAY=5

    (rows migrated from Odoo 14 are single-line). Feeding the whole blob to
    ``vRecur.from_ical`` makes the DTSTART line part of the first key, so
    FREQ comes back as ``'MONTHLY\nRRULE:FREQ'`` and serialisation then aborts
    with "Content line can not contain unescaped new line characters".
    """
    for line in (raw or "").splitlines():
        candidate = line.strip()
        if candidate.upper().startswith("RRULE:"):
            return candidate[6:]
    return (raw or "").strip()


def _add_recurrence(component, event):
    if not event.recurrency or not event.recurrence_id:
        return
    body = rrule_text(event.recurrence_id.rrule)
    if not body:
        return
    try:
        from icalendar.prop import vRecur

        component.add("rrule", vRecur.from_ical(body), encode=0)
    except Exception:
        _logger.warning(
            "dav_server: unparsable rrule on recurrence %s", event.recurrence_id.id
        )
        component.add("rrule", vText(body))


def _add_organizer(component, event):
    partner = event.user_id.partner_id
    if not partner or not partner.email:
        return
    address = _mail_address(partner.email, partner.name)
    component.add("organizer", address, encode=0)


def _add_attendees(component, event):
    states = {
        attendee.partner_id.id: attendee.state
        for attendee in event.attendee_ids
        if attendee.partner_id
    }
    for partner in event.partner_ids:
        if not partner.email:
            continue
        address = _mail_address(partner.email, partner.name)
        state = states.get(partner.id, "needs-action")
        partstat = ODOO_TO_PARTSTAT.get(state, "NEEDS-ACTION")
        address.params["PARTSTAT"] = vText(partstat)
        address.params["ROLE"] = vText("REQ-PARTICIPANT")
        address.params["RSVP"] = vText("TRUE")
        component.add("attendee", address, encode=0)


def _add_privacy(component, event):
    transp = SHOW_AS_TO_TRANSP.get(event.show_as, "OPAQUE")
    if event.privacy == "public":
        transp = "TRANSPARENT"
    component.add("transp", transp)
    component.add("status", "CONFIRMED")
    component.add("class", PRIVACY_TO_CLASS.get(event.privacy, "PRIVATE"))


def _add_alarms(component, event):
    for alarm in event.alarm_ids:
        minutes = alarm.duration_minutes
        if not minutes:
            continue
        subcomponent = Component()
        subcomponent.name = "VALARM"
        component.add_component(subcomponent)
        action = "EMAIL" if alarm.alarm_type == "email" else "DISPLAY"
        subcomponent.add("action", action)
        subcomponent.add("description", alarm.name or "Reminder")
        # RFC 5545: a negative duration means "before DTSTART".
        subcomponent.add("trigger", -timedelta(minutes=minutes))
        partner = event.user_id.partner_id
        if alarm.alarm_type == "email" and partner and partner.email:
            subcomponent.add(
                "attendee", _mail_address(partner.email, partner.name), encode=0
            )


# ======================================================================
# Import
# ======================================================================
def ical_to_event_values(raw, user):
    """Turn a VCALENDAR payload into ``calendar.event`` values.

    Returns values suitable for ``create``; ``dav_uid`` is *not* included --
    the caller resolves the target record from the href and passes the UID in
    explicitly so a rename on the client cannot create a duplicate.

    The private ``_organizer_email`` key carries the ORGANIZER address for the
    caller to resolve; it must be popped before the values reach the ORM.

    Raises :class:`UnsupportedPayload` for payloads Odoo cannot hold.
    """
    calendar = Calendar.from_ical(raw)
    components = calendar.walk("VEVENT")
    if not components:
        raise UnsupportedPayload("payload contains no VEVENT component")

    # Prefer an override component: Thunderbird sends the series master
    # alongside RECURRENCE-ID patches for the edited occurrences.
    overrides = [c for c in components if "RECURRENCE-ID" in c]
    component = overrides[0] if overrides else components[0]

    values = _timing_values(component)
    values["name"] = _text(component.get("SUMMARY")) or "(no title)"

    if component.get("DESCRIPTION") is not None:
        values["description"] = _text(component.get("DESCRIPTION"))[:TEXT_MAX]
    if component.get("LOCATION") is not None:
        values["location"] = _text(component.get("LOCATION"))

    values.update(_privacy_values(component))

    if "RRULE" in component:
        values.update(_recurrence_values(component))
        # event_tz only exists on calendar.event as a pseudo-related field of
        # the recurrence. Writing it on a non-recurring event makes Odoo raise
        # 'Unable to save the recurrence with "This Event"', so it is only sent
        # alongside a recurrence. For one-off events the instant is still stored
        # correctly in UTC and Odoo displays it in the user's own zone.
        values["event_tz"] = timezone_name(component, component.decoded("DTSTART"))
    else:
        values["recurrency"] = False

    partner_ids = _resolve_partner_ids(user, _attendee_addresses(component))
    values["partner_ids"] = [(6, 0, partner_ids)]
    values["alarm_ids"] = _alarm_commands(component)
    values["_organizer_email"] = _organizer_address(component)
    return values


def _organizer_address(component):
    organizer = component.get("ORGANIZER")
    value = str(organizer) if organizer is not None else ""
    if value.lower().startswith("mailto:"):
        return value[7:].strip().lower()
    return ""


def _timing_values(component):
    if component.get("DTSTART") is None:
        raise UnsupportedPayload("VEVENT has no DTSTART")

    start = component.decoded("DTSTART")
    if component.get("DTEND") is not None:
        stop = component.decoded("DTEND")
    elif component.get("DURATION") is not None:
        stop = start + component.decoded("DURATION")
    else:
        stop = start + timedelta(hours=1)

    allday = isinstance(start, date) and not isinstance(start, datetime)
    values = {
        "allday": allday,
        "start": _as_utc_naive(start),
        "stop": _as_utc_naive(stop),
    }
    if values["stop"] < values["start"]:
        raise UnsupportedPayload("VEVENT ends before it starts")
    return values


def timezone_name(component, start):
    """The TZID (or zone of a decoded value) carried by a component's DTSTART."""
    tzid = component["DTSTART"].params.get("TZID") if "DTSTART" in component else None
    return str(tzid) if tzid else _zone_key(start) or "UTC"


def _privacy_values(component):
    values = {}
    transp = _text(component.get("TRANSP")).upper()
    if transp:
        values["show_as"] = TRANSP_TO_SHOW_AS.get(transp, "busy")
    klass = _text(component.get("CLASS")).upper()
    if klass:
        values["privacy"] = CLASS_TO_PRIVACY.get(klass, "private")
    return values


def _recur_list(recur, key):
    """Read a multi-valued key out of an ``icalendar`` ``vRecur``.

    ``vRecur`` is a dict whose values are always lists, so BYDAY arrives as
    ``['TU', 'TH']`` and must not be unwrapped to a single entry.
    """
    value = recur.get(key) or []
    if isinstance(value, (list, tuple)):
        return value
    return [value]


def _recur_value(recur, key, default=None):
    """Read a single-valued key out of an ``icalendar`` ``vRecur``.

    ``str(vRecur)`` is a Python repr rather than an RRULE string, so re-parsing
    it silently drops INTERVAL/UNTIL. Read the parsed mapping directly instead.
    """
    value = recur.get(key, default)
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    return value


def _recurrence_values(component):
    recur = component["RRULE"]
    freq = str(_recur_value(recur, "FREQ", "") or "").lower()
    rrule_type = RRULE_TYPES.get(freq, "weekly")
    values = {
        "recurrency": True,
        "rrule_type": rrule_type,
        "rrule_type_ui": rrule_type,
        "interval": max(1, int(_recur_value(recur, "INTERVAL", 1) or 1)),
    }

    until = _recur_value(recur, "UNTIL")
    count = _recur_value(recur, "COUNT")
    if until:
        values["until"] = until.date() if isinstance(until, datetime) else until
        values["end_type"] = "end_date"
    elif count:
        values["count"] = max(1, int(count))
        values["end_type"] = "count"
    else:
        values["end_type"] = "forever"

    simple_days, nth_weekday = _split_byday(_recur_list(recur, "BYDAY"))
    if simple_days:
        for field, _selection in simple_days:
            values[field] = True
        if not freq:
            values["rrule_type"] = "weekly"
            values["rrule_type_ui"] = "weekly"

    monthdays = _recur_list(recur, "BYMONTHDAY")
    if monthdays:
        values["day"] = max(1, int(monthdays[0]))
        values["month_by"] = "date"
        values["rrule_type"] = "monthly"
        values["rrule_type_ui"] = "monthly"
    elif nth_weekday:
        _weekday, selection, ordinal = nth_weekday
        values["weekday"] = selection
        values["byday"] = _byday_selection(ordinal)
        values["month_by"] = "day"
        values["rrule_type"] = "monthly"
        values["rrule_type_ui"] = "monthly"
    return values


def _split_byday(codes):
    """Split RFC 5545 BYDAY codes into plain weekdays and ``nTH`` pairs."""
    simple = []
    nth = None
    for raw in codes:
        code = str(raw).upper()
        letters = "".join(character for character in code if character.isalpha())
        entry = WEEKDAY_FIELDS.get(letters)
        if not entry:
            _logger.info("dav_server: ignoring unsupported BYDAY code %r", code)
            continue
        ordinal = code[: len(code) - len(letters)]
        if ordinal:
            nth = (letters, entry[1], ordinal)
        else:
            simple.append(entry)
    return simple, nth


def _byday_selection(ordinal):
    try:
        number = int(ordinal)
    except ValueError:
        return "1"
    if -5 <= number <= -1:
        return "-1"
    return str(number) if 1 <= number <= 5 else "1"


def _properties(component, name):
    """Return a component property as a list, whatever icalendar hands back.

    ``icalendar`` 7 returns the property object itself from ``Component.get``
    even for *repeatable* properties such as ``ATTENDEE`` -- and those objects
    subclass ``str``. Iterating one therefore yields characters rather than
    properties, which silently dropped every attendee and fell back to
    ORGANIZER. Normalise both shapes here.
    """
    value = component.get(name)
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _attendee_addresses(component):
    addresses = []
    for raw in _properties(component, "ATTENDEE"):
        value = str(raw)
        if value.lower().startswith("mailto:"):
            addresses.append(value[7:].strip().lower())
    if not addresses:
        organizer = component.get("ORGANIZER")
        value = str(organizer) if organizer else ""
        if value.lower().startswith("mailto:"):
            addresses.append(value[7:].strip().lower())
    return addresses


def _resolve_partner_ids(user, addresses):
    """Map ATTENDEE addresses onto existing partners. Never creates any.

    Creating contacts from an inbound calendar payload would let any
    authenticated device inject arbitrary partners into the address book.
    """
    if not addresses:
        return []
    partners = (
        user.env["res.partner"]
        .sudo()
        .with_context(active_test=False)
        .search([("email", "in", addresses)])
    )
    found = {
        partner.email.strip().lower(): partner.id
        for partner in partners
        if partner.email
    }
    missing = [address for address in addresses if address not in found]
    if missing:
        _logger.info("dav_server: no partner for attendee address(es) %s", missing)
    seen = set()
    ordered = []
    for address in addresses:
        partner_id = found.get(address)
        if partner_id and partner_id not in seen:
            seen.add(partner_id)
            ordered.append(partner_id)
    return ordered


def _alarm_commands(component):
    values_list = []
    for valarm in component.walk("VALARM"):
        trigger = valarm.get("TRIGGER")
        if trigger is None:
            continue
        delta = getattr(trigger, "dt", trigger)
        if not isinstance(delta, timedelta):
            _logger.info("dav_server: ignoring VALARM trigger %r", trigger)
            continue
        minutes = int(-delta.total_seconds() // 60)
        if minutes <= 0:
            _logger.info(
                "dav_server: calendar.alarm is 'before' only, ignoring %r",
                trigger,
            )
            continue
        action = _text(valarm.get("ACTION") or "DISPLAY").upper()
        values_list.append(
            {
                "name": _text(valarm.get("DESCRIPTION")) or "Reminder",
                "alarm_type": "email" if action == "EMAIL" else "notification",
                "duration": _alarm_units(minutes)[0],
                "interval": _alarm_units(minutes)[1],
            }
        )
    return [(0, 0, values) for values in values_list]


def _alarm_units(minutes):
    for size, interval in ALARM_UNITS:
        if minutes >= size and minutes % size == 0:
            return minutes // size, interval
    return minutes, "minutes"


# ======================================================================
# Helpers
# ======================================================================
def _as_date(value):
    return value.date() if isinstance(value, datetime) else value


def _as_utc_naive(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)
    return datetime.combine(value, datetime.min.time())


def _zone_key(value):
    return getattr(getattr(value, "tzinfo", None), "key", None)


def _with_zone(value, zone):
    """Re-express a naive-UTC Odoo datetime in ``zone`` for the wire.

    ``calendar.event.start``/``stop`` are stored as naive UTC. Simply tagging
    that value with the display zone would shift the instant by the UTC offset
    (09:00 UTC would read as 09:00 Bangkok == 02:00 UTC), so the value is first
    pinned to UTC and then converted.
    """
    if not isinstance(value, datetime):
        return value
    naive = (
        value
        if value.tzinfo is None
        else value.astimezone(UTC).replace(tzinfo=None)
    )
    try:
        return naive.replace(tzinfo=UTC).astimezone(ZoneInfo(zone or "UTC"))
    except (ZoneInfoNotFoundError, ValueError):
        return naive.replace(tzinfo=UTC)


def _mail_address(email, name):
    address = vCalAddress(f"mailto:{email}")
    if name:
        address.params["CN"] = vText(name)
    return address


def _plain_text(value):
    from odoo.tools import html2plaintext

    return html2plaintext(value or "")[:TEXT_MAX]


def _text(value):
    return "" if value is None else str(value)


def _public_url(event):
    base_url = event.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
    return f"{base_url}/event/{event.access_token}"
