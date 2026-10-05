Client setup
------------

The service root is ``https://<your-odoo-host>/dav/``. ``/.well-known/caldav``
and ``/.well-known/carddav`` redirect there, so autodiscovery works without
typing a URL, but the redirect target still has to be reachable from the client.

Address the client at the collection URL directly, substituting your own login.
Note that Odoo logins contain ``@`` and sometimes ``+``:

.. code-block:: text

    Calendars:    https://<host>/dav/caldav/<your-login>/
    Address book: https://<host>/dav/carddav/<your-login>/

In practice you rarely type these: after pointing DAVx5 or Thunderbird at
``https://<host>/dav/``, both home sets are discovered from the principal and
you then pick which collections to enable.

Android (DAVx5)
~~~~~~~~~~~~~~~

1. *Add account* ▸ *Log in with URL and username*.
2. Server URL: ``https://<host>/dav/``, username: your Odoo login, password: as
   usual.
3. Choose which calendars and address books to synchronise, then force a sync.
4. On the first run only, use *Settings ▸ Account ▸ Contacts* to push the
   phone's own address book up to Odoo.

Thunderbird
~~~~~~~~~~~

* Calendar ▸ *New Calendar* ▸ *On the Network* ▸ CalDAV.
* Address Book ▸ *New Address Book* ▸ *Network Directory*.

Use the same URL and credentials for both.

Synchronisation model
---------------------

* Writes made on a device go through ``PUT`` and are written to Odoo with
  ``dont_notify`` set, so importing a change never triggers an Odoo invitation
  email or a chatter entry for something the client already knows about.
* Conditional writes are honoured: a ``PUT`` carrying a stale ``If-Match`` ETag
  is rejected with ``412`` instead of clobbering a newer change.
* Incremental sync uses a real change log (``dav.sync.change``) rather than a
  ``write_date`` watermark, so deletions propagate. A client whose token is older
  than the 90-day retention window receives ``409`` plus a ``valid-sync-token``
  header and re-lists, per RFC 6578.
