By default, when importing data (like CSV import) with the `base_import`
module, Odoo follows this rule:

- If you import the XMLID of a record, make an **update**.
- If you do not, **create** a new record.

This module allows you to set additional rules to match if a given
import is an update or a new record.

This is useful when you need to sync heterogeneous databases, and the
field you use to match records in those databases with Odoo's is not the
XMLID but the name, VAT, email, etc.

After installing this module, the import preview UI adds a **Match** column. Checking
the box on a field means:

- Use it to **find existing records** (match key).
- **Do not write** its value during the actual import.

This lets you update records by matching on fields like name, email or VAT without
needing an XMLID in your file.

Pre-configured **Import Match** rules act as templates: their fields are pre-checked in
the import preview. You can toggle any field on or off before importing, regardless of
whether a rule exists.

When match-only fields are selected in the UI, matching uses all selected fields
together to search for a single existing record. If any row fails to match exactly one
record (zero or multiple matches), the entire import is blocked and errors are shown for
the affected rows. This prevents accidental creation of duplicate records.

Note that conditional rules (fields with a required imported value) are only applied
during programmatic imports; the UI-driven matching uses the selected fields
unconditionally.

For programmatic imports (without UI), the configured rules are used instead. The import
logic in that case is:

- If you import the XMLID of a record, make an **update**.
- If you do not:
  - If there are import match rules for the model you are importing:
    - Discard the rules that require fields you are not importing.
    - Traverse the remaining rules one by one in order to find a match
      in the database.
      - Skip the rule if it requires a special condition that is not
        satisfied.
      - If one match is found:
        - Stop traversing the rest of valid rules.
        - **Update** that record.
      - If zero or multiple matches are found:
        - Continue with the next rule.
      - If all rules are exhausted and no single match is found:
        - **Create** a new record.
  - If there are no match rules for your model:
    - **Create** a new record.

By default 2 rules are installed for production instances:

- One rule that will allow you to update companies based on their VAT,
  when `is_company` is `True`.
- One rule that will allow you to update users based on their login.

In demo instances there are more examples.
