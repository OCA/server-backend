This module serves CalDAV (RFC 4791) and CardDAV (RFC 6352) directly from
Odoo, so phones and desktop clients can sync events and contacts two-way
against records that stay in the Odoo database.

It exists because the OCA ``base_dav`` module cannot do this: its Radicale
integration targets Radicale 2.x (``radicale.config.INITIAL_CONFIG``,
``radicale.rights.AuthenticatedRights``), and Radicale 3.0 replaced those APIs.
That module's ``/.dav`` route is therefore disabled in this repository and the
scanner upload endpoint it used to share is served separately by ``bureaucracy``.

Access control is delegated to Odoo's own record rules rather than to the URL.
A collection's domain is evaluated with ``user`` bound to the authenticated DAV
user, and the search runs under their access rights, so a collection URL never
grants more than the user's Odoo rights do.

## Odoo quirks worth knowing about

Three upstream behaviours shaped this implementation and are worth calling out,
because each one silently produces wrong data rather than an error:

1. ``calendar.event.event_tz`` is recurrence-only. Writing it on a one-off event
   raises ``UserError``.
2. ``calendar.recurrence.rrule`` holds a two-line ``DTSTART``/``RRULE`` blob.
   Passing it whole to ``icalendar`` folds the ``DTSTART`` line into the first
   key, so ``FREQ`` comes back mangled.
3. ``calendar.event.start``/``stop`` are naive **UTC**. Re-tagging them with a
   display timezone without converting first shifts every event by the UTC
   offset.

Odoo's own ``_get_ics_file`` (used for invitation emails) additionally emits
VALARM triggers with a positive duration, which RFC 5545 reads as "after the
start" even though the field is called "Remind Before". This module emits the
spec-correct negative duration.
