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
            newdata = list()
            # Data conversion to ORM format
            import_fields = list(map(models.fix_import_export_id_paths, fields))
            converted_data = self._convert_records(
                self._extract_records(import_fields, data)
            )
            # Mock Odoo to believe the user is importing the ID field
            if "id" not in fields:
                fields.append("id")
            # Needed to match with converted data field names
            for dbid, xmlid, record, info in converted_data:
                # In case of one2many on empty lines one record may contain several rows
                for row_index in range(info["rows"]["from"], info["rows"]["to"] + 1):
                    row = dict(zip(fields, data[row_index]))
                    match = self
                    if xmlid:
                        # Skip rows with ID, they do not need all this
                        row["id"] = xmlid
                        newdata.append(tuple(row[f] for f in fields))
                        continue
                    elif dbid:
                        # Find the xmlid for this dbid
                        match = self.browse(dbid)
                    elif row_index == info["rows"]["from"]:
                        # Store records that match a combination
                        # But only for first row of record,
                        # because the rest contain one2many fields
                        match = self.env["base_import.match"]._match_find(
                            self, record, row
                        )
                    # Give a valid XMLID to this row if a match was found
                    # To generate externals IDS.
                    match.export_data(fields)
                    ext_id = match.get_external_id()
                    row["id"] = ext_id[match.id] if match else row.get("id", "")
                    # Store the modified row, in the same order as fields
                    newdata.append(tuple(row[f] for f in fields))
            # We will import the patched data to get updates on matches
            data = newdata
        # Normal method handles the rest of the job
        return super(Base, self).load(fields, data)
