# Copyright 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def load(self, fields, data):
        """Try to identify rows by other pseudo-unique keys.

        It searches for rows that have no XMLID specified, and gives them
        one if any :attr:`~.field_ids` combination is found. With a valid
        XMLID in place, Odoo will understand that it must *update* the
        record instead of *creating* a new one.
        """
        # We only need to patch this call if there are usable rules for it
        if self.env["base_import.match"]._usable_rules(self._name, fields):
            # Copy rows, as matched rows get their ID column patched in place.
            data = [list(row) for row in data]
            # Change .id (dbid) by id (xmlid)
            if ".id" in fields:
                column = fields.index(".id")
                fields[column] = "id"
                # data[0][column] = "id"
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
                self._extract_records(import_fields, data)
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
                else:
                    # Store records that match a combination
                    match = self.env["base_import.match"]._match_find(self, record, row)
                # Give a valid XMLID to this row if a match was found
                # To generate externals IDS.
                match.export_data(fields)
                if match:
                    first_row[id_index] = match.get_external_id()[match.id]
        # Normal method handles the rest of the job
        return super().load(fields, data)
