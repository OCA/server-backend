Known issues / Roadmap
======================

* No iTIP. An inbound ``PARTSTAT`` is recorded on ``calendar.attendee.state``,
  but the server never emits ``REQUEST``/``REPLY``/``CANCEL`` messages. Odoo's
  own invitation emails (which use ``vobject``) are unaffected.
* ``RECURRENCE-ID`` overrides are flattened. Editing one occurrence of a series
  from a client creates a standalone event rather than a true series exception,
  so Odoo shows it separately from the series. Editing the whole series works
  normally.
* Only ``VEVENT`` round-trips. ``VTODO`` and ``VJOURNAL`` are advertised as
  supported components (Odoo has no model for them) but a ``PUT`` containing one
  is rejected with ``415``-class semantics via ``UnsupportedPayload``.
* Reminders are "before" only. Odoo's ``calendar.alarm`` has no notion of a
  reminder that fires after an event, so a positive VALARM ``TRIGGER`` is
  dropped with a log line rather than being silently inverted.
* ``VTODO``/``VTJOURNAL`` reminders in incoming VALARMs are ignored.
* Embedded ``PHOTO`` is written from the stored ``image_1920`` without
  re-encoding, so the ``TYPE`` parameter is sniffed from the leading magic
  bytes (JPEG/PNG/GIF) and anything unrecognised is declared ``JPEG``. The
  importer deliberately does not round-trip ``PHOTO`` back, because Odoo has no
  way to tell which avatar field a device meant.
* ``PROPFIND`` always answers with every property the server knows, rather than
  filtering to the ones the client asked for. Clients accept this, but it is
  more traffic than RFC 4918 requires.
* Remote collection creation (``MKCALENDAR``/``MKCOL``) is not implemented;
  collections are created in the Odoo UI.
* One-off events carry no timezone of their own. In Odoo 17 ``calendar.event``
  keeps ``event_tz`` as a pseudo-related field of the recurrence, so it is
  ``False`` for anything that is not a recurring series and writing it raises
  ``Unable to save the recurrence with "This Event"``. The instant is still
  stored correctly in UTC; the export labels it with the *organiser's* zone,
  which is what the Odoo web client displays too. A ``TZID`` sent by a client
  for a non-recurring event is therefore dropped on import.
* ``calendar.recurrence.rrule`` is stored over two lines (``DTSTART:`` then
  ``RRULE:``) by Odoo 17, not the single line Odoo 14 produced. Both are handled,
  but any other consumer of that column should know.
* The ``rights`` field on a calendar/addressbook collection is metadata only.
  Access is decided by the collection domain combined with Odoo's record rules;
  the field is not consulted.
* ``base_dav`` remains installed because ``bureaucracy`` depends on it for the
  scanner's files-only ``/.dav`` endpoint and for the shared ``dav.collection``
  model. Its unused Radicale plugin layer, and the ``radicale``/``vobject``
  requirements that go with it, are dead weight that could be dropped
  separately.