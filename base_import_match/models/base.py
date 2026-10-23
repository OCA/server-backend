# Copyright 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _match_by_fields(self, match_fields, converted_row, imported_row):
        """Find existing records matching on the given fields.

        Return a ``(recordset, count)`` tuple. When exactly one record matches,
        *recordset* is that record; otherwise it is an empty record.
        """
        domain = []
        for fname in match_fields & converted_row.keys():
            value = converted_row[fname]
            # For x2many fields
            if isinstance(value, list) and value and isinstance(value[0], tuple):
                for ref in imported_row.get(fname, "").split(","):
                    ref = ref.strip()
                    if ref:
                        domain.append((fname, "=", ref))
            else:
                domain.append((fname, "=", value))
        if not domain:
            return self, 0
        match = self.search(domain, limit=2)
        if len(match) == 1:
            return match, 1
        return self, len(match)

    @api.model
    def _match_error(self, match_fields, row, info, count):
        """Build an import error dict for a failed match attempt."""
        criteria = ", ".join(f"{f}={row.get(f, '')}" for f in sorted(match_fields))
        if count == 0:
            msg = self.env._(
                "No matching record found for: %(criteria)s", criteria=criteria
            )
        else:
            msg = self.env._(
                "Multiple matching records found (expected 1) for: %(criteria)s",
                criteria=criteria,
            )
        return {
            "type": "error",
            "message": msg,
            "rows": info["rows"],
            "record": info["record"],
            "field": False,
        }

    @api.model
    def load(self, fields, data):
        """Try to identify rows by other pseudo-unique keys.

        It searches for rows that have no XMLID specified, and gives them
        one if any :attr:`~.field_ids` combination is found. With a valid
        XMLID in place, Odoo will understand that it must *update* the
        record instead of *creating* a new one.
        """
        # UI-selected match fields prevail; configured rules are only used when the
        # context key is absent (e.g. programmatic imports).
        ctx_match_only = self.env.context.get("import_match_only_fields")
        match_only_fields = set(ctx_match_only or []) & set(fields)
        has_rules = ctx_match_only is None and bool(
            self.env["base_import.match"]._usable_rules(self._name, fields)
        )
        if match_only_fields or has_rules:
            # Work on local copies so we don't mutate the caller's lists
            # (core reuses them after load() to report imported record names).
            fields = list(fields)
            data = [list(row) for row in data]
            match_errors = []
            # Change .id (dbid) by id (xmlid)
            if ".id" in fields:
                column = fields.index(".id")
                fields[column] = "id"
                for values in data:
                    dbid = int(values[column])
                    values[column] = self.browse(dbid).get_external_id().get(dbid)
            # Mock Odoo to believe the user is importing the ID field. Add the
            # column before extracting records, as the extraction is lazy and
            # expects rows as wide as the field list.
            if "id" not in fields:
                fields.append("id")
                for values in data:
                    values.append("")
            id_index = fields.index("id")
            # Data conversion to ORM format
            import_fields = list(map(models.fix_import_export_id_paths, fields))
            converted_data = self._convert_records(
                self._extract_records(import_fields, data),
                savepoint=self.env.cr.savepoint(),
            )
            # Needed to match with converted data field names
            clean_fields = [f[0] for f in import_fields]
            for dbid, xmlid, record, info in converted_data:
                if xmlid:
                    # Skip rows with ID, they do not need all this
                    continue
                # A record with one2many lines spans several rows. Only the
                # first row holds the record values and its ID.
                first_row = data[info["rows"]["from"]]
                row = dict(zip(clean_fields, first_row, strict=False))
                match = self
                if dbid:
                    # Find the xmlid for this dbid
                    match = self.browse(dbid)
                elif match_only_fields:
                    # Match using user-selected fields from the UI
                    match, count = self._match_by_fields(match_only_fields, record, row)
                    if count != 1:
                        match_errors.append(
                            self._match_error(match_only_fields, row, info, count)
                        )
                else:
                    # Store records that match a combination
                    match = self.env["base_import.match"]._match_find(self, record, row)
                # Give a valid XMLID to this row if a match was found
                # To generate externals IDS.
                match.export_data(fields)
                if match:
                    first_row[id_index] = match.get_external_id()[match.id]
            if match_errors:
                return {"ids": False, "messages": match_errors, "nextrow": False}
            # Rebuild fields/data without match-only columns.
            if match_only_fields:
                drop_set = {fields.index(f) for f in match_only_fields}
                keep_indexes = [i for i in range(len(fields)) if i not in drop_set]
                fields[:] = [fields[i] for i in keep_indexes]
                data = [tuple(row[i] for i in keep_indexes) for row in data]
        # Normal method handles the rest of the job
        return super().load(fields, data)
