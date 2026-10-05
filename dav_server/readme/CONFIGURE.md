Collection
----------

Go to *Settings ▸ WebDAV Collections* and add a record per calendar you want to
expose.

============================  =============================================
Field                         Notes
============================  =============================================
Name                          Shown to the client as the calendar name.
Type                          ``Calendar`` or ``Addressbook``. ``Files``
                              collections are handled by ``bureaucracy``.
Model                         ``calendar.event`` for calendars,
                              ``res.partner`` for address books.
DAV Slug                      Derived from the name; the URL segment. Two
                              collections with the same name get ``-2``,
                              ``-3`` suffixes.
Domain                        Which records the collection exposes. May
                              reference ``user`` in its Python context, e.g.
                              ``[('user_id', '=', user.id)]``.
Rights                        Metadata only for calendar/addressbook
                              collections. Access is decided by the domain
                              combined with Odoo's record rules.
============================  =============================================

A typical personal calendar uses:

.. code-block:: python

    [('user_id', '=', user.id)]

A shared family address book should be gated on an explicit partner category so
that nothing leaks by accident:

.. code-block:: python

    [('category_id', 'in', [address_book_category.id])]

Authentication
--------------

Clients send HTTP Basic credentials. Two consequences:

* An account with two-factor authentication enabled is refused with ``401``.
  CalDAV has nowhere to prompt for a one-time code, so the account is rejected
  up front with a logged reason rather than failing silently on every sync.
* Portal users are refused with ``403``. They can reach the web client but must
  not enumerate internal records.
