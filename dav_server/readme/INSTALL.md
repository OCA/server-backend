To use this module, you need to:

1. Install the ``calendar`` and ``contacts`` apps so that ``calendar.event``
   and the partner address book exist.
2. Configure at least one DAV collection under *Settings ▸ WebDAV
   Collections*, choosing type ``Calendar`` or ``Addressbook`` and pointing it
   at ``calendar.event`` or ``res.partner``.

No external account or credential store is involved: clients authenticate with
their normal Odoo login and password over HTTP Basic.

For Android, use `DAVx5 <https://www.davx5.com/>`_. For desktop, Thunderbird
speaks CalDAV and CardDAV natively (Calendar ▸ New Calendar ▸ On the Network,
Address Book ▸ New Address Book ▸ Network Directory).
