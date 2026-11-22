To configure this module, you need to:

1. Go to Settings / Technical / Anonymization / Field Definitions
2. Review fields to overwrite: every field can be overwritten by some method, and the overwritten records can be restricted by a domain

Domains are evaluated with three variables: `protected_partner_ids`, the partners of the companies, OdooBot and the public users, which the default definitions leave untouched, `admin_user_ids`, the superuser and the administrator, and `protected_user_ids`, the same plus the public users.

Methods that take options read them from the *Options* column, a JSON object overriding the defaults shown in *Default options*. The *Pattern with record id* method replaces `{id}` with the record's id, so `partner{id}@example.com` gives every partner a distinct address that cannot receive mail. The *Faker provider* method generates values with [Faker](https://faker.readthedocs.io): `{"provider": "iban"}` gives valid IBANs, `{"provider": "vat_id", "locale": "it_IT"}` valid Italian VAT numbers; `kwargs` are passed to the provider, and `"unique": true` avoids repeated values on columns with a unique constraint. The default definitions use it for bank account numbers and Italian fiscal codes; VAT numbers are emptied instead, since their format depends on the partner's country.

Definitions for fields of modules that are not installed are kept and simply not applied. *Recompute stored computed field* definitions rebuild the stored copies of anonymized values (`complete_name`, `email_normalized`, ...): give them a higher sequence than the fields they are computed from.

The definitions for the descriptions of invoice, sale and purchase lines are inactive by default: those descriptions often quote the customer, but replacing them makes the documents harder to read. Activate them (filter on *Archived*) to replace each description with the name of the line's product, or with `Line {id}` on lines without product.
