This module provides a flexible mechanism and default configuration for anonymizing data in an Odoo database.

Unlike `odoo-bin obfuscate`, which encrypts values with a password and can be reversed, the overwrite is irreversible: the result is anonymized, not pseudonymized, data.

Not to be confused with `base_db_anonymization` by Mint System, a separate module with a similar name. This one has pluggable methods, default definitions for the core modules (partners, users, bank accounts, chatter and tracking values, mail queue, calendar, CRM, invoices, sales, purchases, projects, Italian e-invoicing, attachments), writes in SQL rather than record by record, and refuses to run on a database that was not neutralized.
