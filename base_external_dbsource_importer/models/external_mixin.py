# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from psycopg2.extensions import AsIs

from odoo import api, models


class DbsourceExternalMixin(models.AbstractModel):
    """Provides utilities for identifying records using a unique external key."""

    _name = "dbsource.external.mixin"
    _description = "Mixin for models that need to map external records"

    @api.model
    def search_external(self, key_value, field_key):
        """
        Mapped model is an model to mapp external records to only one
        """
        mapped_model = self.env.context.get("mapped_model")
        if mapped_model:
            domain = [("external_key", "=", key_value)]
            mapped = self.env[mapped_model].search(domain)
            if mapped:
                key_value = mapped.mapped_key
        domain = [(field_key, "=", key_value)]
        return self.with_context(active_test=False).search(domain)

    def create_bypassed(self, vals_list):  # noqa: C901
        # From v12 create method
        bad_names = {"id", "parent_path"}
        if self._log_access:
            bad_names.update(models.LOG_ACCESS_COLUMNS)
        unknown_names = set()
        data_list = []
        inversed_fields = set()
        for vals in vals_list:
            # add missing defaults
            vals = self._add_missing_default_values(vals)
            # distribute fields into sets for various purposes
            data = {}
            data["stored"] = stored = {}
            data["inversed"] = inversed = {}
            data["inherited"] = inherited = defaultdict(dict)
            data["protected"] = protected = set()
            for key, val in vals.items():
                if key in bad_names:
                    continue
                field = self._fields.get(key)
                if not field:
                    unknown_names.add(key)
                    continue
                if field.store:
                    stored[key] = val
                if field.inherited:
                    inherited[field.related_field.model_name][key] = val
                elif field.inverse:
                    inversed[key] = val
                    inversed_fields.add(field)
                    protected.update(self._field_computed.get(field, [field]))
            data_list.append(data)

        # From v12 _create method
        # Create records from the stored field values in ``data_list``.
        assert data_list
        cr = self.env.cr
        quote = '"{}"'.format

        # set boolean fields to False by default (avoid NULL in database)
        for name, field in self._fields.items():
            if field.type == "boolean" and field.store:
                for data in data_list:
                    data["stored"].setdefault(name, False)

        # insert rows
        ids = []  # ids of created records
        other_fields = set()  # non-column fields
        translated_fields = set()  # translated fields

        # column names, formats and values (for common fields)
        columns0 = [("id", "nextval(%s)", self._sequence)]
        if self._log_access:
            columns0.append(("create_uid", "%s", self._uid))
            columns0.append(("create_date", "%s", AsIs("(now() at time zone 'UTC')")))
            columns0.append(("write_uid", "%s", self._uid))
            columns0.append(("write_date", "%s", AsIs("(now() at time zone 'UTC')")))

        for data in data_list:
            # determine column values
            columns = list(columns0)
            for name, val in sorted(data["stored"].items()):
                field = self._fields[name]
                assert field.store

                if field.column_type:
                    col_val = field.convert_to_column(val, self, data["stored"])
                    columns.append((name, field.column_format, col_val))
                    if field.translate is True:
                        translated_fields.add(field)
                else:
                    other_fields.add(field)

            # insert a row with the given columns
            # pylint: disable=E8103
            query = "INSERT INTO {} ({}) VALUES ({}) RETURNING id".format(
                quote(self._table),
                ", ".join(quote(name) for name, fmt, val in columns),
                ", ".join(fmt for name, fmt, val in columns),
            )
            params = [val for name, fmt, val in columns]
            cr.execute(query, params)
            ids.append(cr.fetchone()[0])

            # Compatibility v11 and v12
            if other_fields:
                record = self.browse(ids[-1])
                protected_fields = protected
                upd_todo = [field.name for field in other_fields]

                # From v11 _create method
                with self.env.protecting(protected_fields, record):
                    # defaults in context must be removed when call a
                    # one2many or many2many
                    rel_context = {
                        key: val
                        for key, val in self._context.items()
                        if not key.startswith("default_")
                    }
                    # call the 'write' method of fields which are not columns
                    for name in sorted(
                        upd_todo, key=lambda name: self._fields[name]._sequence
                    ):
                        field_value = data["stored"].get(name, False)
                        if not field_value:
                            continue
                        field = self._fields[name]
                        field.write(record.with_context(**rel_context), field_value)
        return self.browse(ids)
