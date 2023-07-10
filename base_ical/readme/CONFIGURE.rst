To configure this module, you need to:

#. Go to Settings/Technical/iCalendars
#. Create a calendar, fill in the model you want to expose and possibly a domain to restrict records. You can use the ``user`` variable to restrict things relative to the user using the calendar
#. A few iCalendar-fields have defaults that should work for any model, you'll have to fill in expressions manually though for the start and end date of the records.

   For example, for model ``calendar.event``, you'd fill in ``record.allday and record.start_date or record.start`` as `DTSTART` and ``record.allday and record.stop_date or record.stop`` as `DTEND`.

   For model ``hr.leave``, you'd write ``(record.request_unit_half or record.request_unit_hours) and record.date_from or record.date_from.date()`` for `DTSTART` and ``(record.request_unit_half or record.request_unit_hours) and record.date_to or (record.date_to.date() + timedelta(days=1))`` for `DTEND` - this is a bit more complex because of the way Odoo handles the begin and end times of leaves, and you'll want the extra day as most clients interpret the end date as non-inclusive.
#. Existing calendars are available for users in the tab `Calendars` of their profile form, where they can enable them to obtain a link they can paste into whatever client they are going to use
