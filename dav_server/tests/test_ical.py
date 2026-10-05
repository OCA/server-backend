# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo.tests import TransactionCase, tagged

from .. import ical


@tagged("post_install", "-at_install")
class TestIcal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Ross Golder",
                "login": "ical-tester",
                "email": "ical.tester@example.com",
                "tz": "Asia/Bangkok",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Attendee One", "email": "attendee.one@example.com"}
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def test_export_basic_event(self):
        event = self._event()
        event.write({"partner_ids": [(6, 0, self.partner.ids)]})
        raw = ical.event_to_ical(event).decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", raw)
        self.assertIn("BEGIN:VEVENT", raw)
        self.assertIn(f"UID:{event.dav_uid}", raw)
        self.assertIn("SUMMARY:Owned by Tester", raw)
        # Odoo stores start as naive UTC; the export re-expresses it in the
        # organiser's zone (Asia/Bangkok, +07:00) without shifting the instant.
        self.assertIn("DTSTART;TZID=Asia/Bangkok:20260105T160000", raw)
        self.assertIn(":mailto:attendee.one@example.com", raw)
        self.assertIn("PARTSTAT=NEEDS-ACTION", raw)
        self.assertIn('ROLE=REQ-PARTICIPANT', raw)
        self.assertIn('ORGANIZER;CN="Ross Golder":mailto:ical.tester@example.com', raw)

    def test_export_emits_vtimezone_for_non_utc_event(self):
        """event_tz is recurrence-only, so the organiser's tz is used instead."""
        event = self._event()
        self.assertFalse(event.event_tz, "Odoo leaves event_tz False here")
        self.assertEqual(ical.event_timezone(event), "Asia/Bangkok")
        raw = ical.event_to_ical(event).decode("utf-8")
        self.assertIn("BEGIN:VTIMEZONE", raw)
        self.assertIn("TZID:Asia/Bangkok", raw)
        self.assertIn("DTSTART;TZID=Asia/Bangkok:20260105T160000", raw)

    def test_export_all_day_uses_date_values(self):
        event = self.env["calendar.event"].create(
            {
                "name": "All Day",
                "allday": True,
                "start": "2026-01-05 00:00:00",
                "stop": "2026-01-06 00:00:00",
                "user_id": self.user.id,
            }
        )
        raw = ical.event_to_ical(event).decode("utf-8")
        self.assertIn("DTSTART;VALUE=DATE:20260105", raw)
        self.assertIn("DTEND;VALUE=DATE:20260106", raw)

    def test_export_emits_negative_alarm_trigger(self):
        event = self._event()
        alarm = self.env["calendar.alarm"].create(
            {
                "name": "Reminder",
                "alarm_type": "notification",
                "duration": 15,
                "interval": "minutes",
            }
        )
        event.write({"alarm_ids": [(4, alarm.id)]})
        raw = ical.event_to_ical(event).decode("utf-8")
        self.assertIn("BEGIN:VALARM", raw)
        # RELATED=START is the RFC 5545 default and icalendar omits it.
        self.assertIn("TRIGGER:-PT15M", raw)

    def test_export_recurrence_uses_single_vevent_with_rrule(self):
        event = self._event()
        event.write(
            {
                "recurrency": True,
                "rrule_type": "monthly",
                "rrule_type_ui": "monthly",
                "interval": 1,
                "count": 10,
                "end_type": "count",
                "month_by": "date",
                "day": 5,
            }
        )
        raw = ical.event_to_ical(event).decode("utf-8")
        self.assertEqual(raw.count("BEGIN:VEVENT"), 1, "a series must be one VEVENT")
        self.assertIn("RRULE:FREQ=MONTHLY", raw)
        self.assertIn("BYMONTHDAY=5", raw)

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def test_import_resolves_every_attendee(self):
        """ATTENDEE is repeatable; a single value must not be iterated."""
        second = self.env["res.partner"].create(
            {"name": "Attendee Two", "email": "attendee.two@example.com"}
        )
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:multi-attendee\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:Two People\r\n"
            "ATTENDEE;PARTSTAT=ACCEPTED:mailto:attendee.one@example.com\r\n"
            "ATTENDEE;PARTSTAT=DECLINED:mailto:attendee.two@example.com\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        resolved = self.env["res.partner"].browse(values["partner_ids"][0][2])
        self.assertEqual(
            set(resolved.mapped("email")),
            {"attendee.one@example.com", "attendee.two@example.com"},
        )
        self.assertIn(second, resolved)

    def test_properties_helper_handles_single_and_list(self):
        from icalendar import Calendar

        single = Calendar.from_ical(
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:u\r\nDTSTART:20260210T090000Z\r\n"
            "ORGANIZER:mailto:me@example.com\r\n"
            "ATTENDEE:mailto:them@example.com\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        ).walk("VEVENT")[0]
        self.assertEqual(len(ical._properties(single, "ATTENDEE")), 1)
        self.assertEqual(len(ical._properties(single, "ORGANIZER")), 1)
        self.assertEqual(ical._properties(single, "MISSING"), [])

    def test_import_simple_event(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n"
            "BEGIN:VEVENT\r\nUID:imported-1\r\n"
            "DTSTAMP:20260101T000000Z\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T103000Z\r\n"
            "SUMMARY:Imported Meeting\r\nLOCATION:Room 1\r\n"
            "DESCRIPTION:Some notes\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["name"], "Imported Meeting")
        self.assertEqual(values["location"], "Room 1")
        self.assertEqual(values["description"], "Some notes")
        self.assertEqual(values["start"], datetime(2026, 2, 10, 9, 0, 0))
        self.assertEqual(values["stop"], datetime(2026, 2, 10, 10, 30, 0))
        self.assertFalse(values["allday"])

    def test_import_weekly_rrule_maps_to_odoo_fields(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:recurring-1\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:Weekly\r\n"
            "RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=8;BYDAY=TU,TH\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertTrue(values["recurrency"])
        self.assertEqual(values["rrule_type"], "weekly")
        self.assertEqual(values["rrule_type_ui"], "weekly")
        self.assertEqual(values["interval"], 2)
        self.assertEqual(values["count"], 8)
        self.assertEqual(values["end_type"], "count")
        self.assertTrue(values["tue"])
        self.assertTrue(values["thu"])
        self.assertFalse(values.get("mon"))

    def test_import_nth_weekday_rrule(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:recurring-2\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:Third Tuesday\r\n"
            "RRULE:FREQ=MONTHLY;BYDAY=3TU;COUNT=6\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["rrule_type"], "monthly")
        self.assertEqual(values["weekday"], "TUE")
        self.assertEqual(values["byday"], "3")
        self.assertEqual(values["month_by"], "day")

    def test_import_until_rrule(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:recurring-3\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:Until\r\n"
            "RRULE:FREQ=DAILY;UNTIL=20260301T000000Z\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["end_type"], "end_date")
        self.assertEqual(str(values["until"]), "2026-03-01")

    def test_import_infinite_rrule_maps_to_forever(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:recurring-4\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:Forever\r\n"
            "RRULE:FREQ=DAILY\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["end_type"], "forever")

    def test_import_rejects_payload_without_vevent(self):
        payload = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        with self.assertRaises(ical.UnsupportedPayload):
            ical.ical_to_event_values(payload, self.user)

    def test_import_all_day_event(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:allday-1\r\n"
            "DTSTART;VALUE=DATE:20260210\r\nDTEND;VALUE=DATE:20260211\r\n"
            "SUMMARY:Holiday\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertTrue(values["allday"])
        self.assertEqual(values["start"], datetime(2026, 2, 10, 0, 0, 0))
        self.assertEqual(values["stop"], datetime(2026, 2, 11, 0, 0, 0))

    def test_rrule_text_splits_the_dtstart_line(self):
        """Odoo 17 stores calendar.recurrence.rrule over two lines."""
        stored = (
            "DTSTART:20261005T102000\n"
            "RRULE:FREQ=MONTHLY;INTERVAL=2;COUNT=5;BYMONTHDAY=5"
        )
        self.assertEqual(
            ical.rrule_text(stored),
            "FREQ=MONTHLY;INTERVAL=2;COUNT=5;BYMONTHDAY=5",
        )
        # Odoo 14 migration leftovers are single-line and must still work.
        self.assertEqual(
            ical.rrule_text("FREQ=WEEKLY;COUNT=4;BYDAY=WE"),
            "FREQ=WEEKLY;COUNT=4;BYDAY=WE",
        )
        self.assertEqual(ical.rrule_text(""), "")
        self.assertEqual(ical.rrule_text(None), "")

    def test_import_alarm_units_round_trip(self):
        self.assertEqual(ical._alarm_units(15), (15, "minutes"))
        self.assertEqual(ical._alarm_units(120), (2, "hours"))
        self.assertEqual(ical._alarm_units(2880), (2, "days"))
        self.assertEqual(ical._alarm_units(90), (90, "minutes"))

    def test_import_ignores_after_alarm(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:alarm-after\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:After\r\n"
            "BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:Late\r\n"
            "TRIGGER;RELATED=START:PT10M\r\nEND:VALARM\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        self.assertEqual(values["alarm_ids"], [])

    def test_import_never_creates_partners(self):
        payload = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
            "BEGIN:VEVENT\r\nUID:unknown-attendee\r\n"
            "DTSTART:20260210T090000Z\r\nDTEND:20260210T100000Z\r\n"
            "SUMMARY:With stranger\r\n"
            "ATTENDEE:mailto:nobody.at.all@example.invalid\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        before = self.env["res.partner"].sudo().search_count(
            [("email", "=", "nobody.at.all@example.invalid")]
        )
        values = ical.ical_to_event_values(payload.encode("utf-8"), self.user)
        after = self.env["res.partner"].sudo().search_count(
            [("email", "=", "nobody.at.all@example.invalid")]
        )
        self.assertEqual(before, after, "a DAV import must not create partners")
        self.assertEqual(values["partner_ids"], [(6, 0, [])])

    # ------------------------------------------------------------------
    # Round trip
    # ------------------------------------------------------------------
    def test_export_then_import_preserves_core_fields(self):
        event = self._event(start="2026-03-15 12:00:00", stop="2026-03-15 13:30:00")
        event.write(
            {
                "location": "Bangkok Office",
                "description": "<p>Bring <b>paper</b></p>",
                "partner_ids": [(6, 0, self.partner.ids)],
                "show_as": "busy",
                "privacy": "private",
            }
        )
        raw = ical.event_to_ical(event)
        values = ical.ical_to_event_values(raw, self.user)
        self.assertEqual(values["name"], event.name)
        self.assertEqual(values["location"], "Bangkok Office")
        self.assertEqual(values["start"], event.start)
        self.assertEqual(values["stop"], event.stop)
        # Odoo's html2plaintext renders <b> as *bold*, the same text the
        # core _get_ics_file() generator puts in an invitation.
        self.assertEqual(values["description"], "Bring *paper*")
        resolved = self.env["res.partner"].browse(values["partner_ids"][0][2])
        self.assertTrue(resolved)
        self.assertEqual(set(resolved.mapped("email")), {self.partner.email})
        self.assertEqual(values["show_as"], "busy")
        self.assertEqual(values["privacy"], "private")

    def test_recurring_series_survives_round_trip(self):
        event = self._event()
        event.write(
            {
                "recurrency": True,
                "rrule_type": "monthly",
                "rrule_type_ui": "monthly",
                "interval": 2,
                "count": 5,
                "end_type": "count",
                "month_by": "date",
                "day": 5,
            }
        )
        raw = ical.event_to_ical(event)
        values = ical.ical_to_event_values(raw, self.user)
        for key in ("rrule_type", "interval", "count", "end_type", "month_by", "day"):
            self.assertEqual(values[key], event.recurrence_id[key], f"{key} differs")

    def _event(
        self,
        start="2026-01-05 09:00:00",
        stop="2026-01-05 10:00:00",
        event_tz="UTC",
    ):
        return self.env["calendar.event"].create(
            {
                "name": "Owned by Tester",
                "start": start,
                "stop": stop,
                "event_tz": event_tz,
                "user_id": self.user.id,
            }
        )
