# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging

from odoo import models
from odoo.tools import SQL, split_every

_logger = logging.getLogger(__name__)


class AnonymizeMethod(models.AbstractModel):
    _name = "anonymize.method"
    _description = "Anonymization method"

    # options a method accepts, with their defaults; anonymize.field.options
    # holds a JSON object overriding them
    _default_options = {}

    def _run(self, field):
        """Overwrite field.field_name on the records selected by field.
        Return the number of rows touched."""
        raise NotImplementedError()

    def _get_model(self, field):
        return self.env[field.model_name].with_context(active_test=False).sudo()

    def _get_query(self, field):
        return self._get_model(field)._where_calc(field._get_domain())

    def _is_stored(self, field):
        model_field = self._get_model(field)._fields[field.field_name]
        return bool(model_field.store and model_field.column_type)

    def _update(
        self,
        field,
        value,
        from_clause=None,
        where=None,
        skip_null=True,
        check_stored=True,
    ):
        """UPDATE the column of field to the SQL expression value, on the records
        selected by field. value may refer to the row as the model's table.
        check_stored=False is for columns the ORM does not declare as stored,
        like res_users.password."""
        if check_stored and not self._check_stored(field):
            return 0
        table = SQL.identifier(self._get_model(field)._table)
        column = SQL.identifier(field.field_name)
        value = self._wrap_translated(field, value)
        conditions = self._get_conditions(field, skip_null)
        if where:
            conditions.append(where)
        self.env.cr.execute(
            SQL(
                "UPDATE %s SET %s = %s%s WHERE %s",
                table,
                column,
                value,
                SQL(" FROM %s", from_clause) if from_clause else SQL(),
                SQL(" AND ").join(conditions),
            )
        )
        return self.env.cr.rowcount

    def _update_values(self, field, generate, skip_null=True, batch_size=10000):
        """Set the column of field, on the records selected by field, to values
        computed in Python by generate(), called once per row. The values are
        written in batches of UPDATE ... FROM (VALUES ...), not record by record."""
        if not self._check_stored(field):
            return 0
        table = SQL.identifier(self._get_model(field)._table)
        column = SQL.identifier(field.field_name)
        self.env.cr.execute(
            SQL(
                "SELECT %s.id FROM %s WHERE %s ORDER BY %s.id",
                table,
                table,
                SQL(" AND ").join(self._get_conditions(field, skip_null)),
                table,
            )
        )
        ids = [row[0] for row in self.env.cr.fetchall()]
        value = self._wrap_translated(field, SQL("new.value"))
        for batch in split_every(batch_size, ids):
            self.env.cr.execute(
                SQL(
                    "UPDATE %s SET %s = %s FROM (VALUES %s) AS new (id, value) "
                    "WHERE %s.id = new.id",
                    table,
                    column,
                    value,
                    SQL(", ").join(SQL("(%s, %s)", id_, generate()) for id_ in batch),
                    table,
                )
            )
        return len(ids)

    def _check_stored(self, field):
        if self._is_stored(field):
            return True
        _logger.warning(
            "%s.%s is not stored, %s skips it",
            field.model_name,
            field.field_name,
            self._name,
        )
        return False

    def _wrap_translated(self, field, value):
        """The SQL expression for value as the content of the column of field:
        translated fields hold a JSON object, with the value as en_US."""
        model_field = self._get_model(field)._fields[field.field_name]
        if getattr(model_field, "translate", False):
            return SQL("jsonb_build_object('en_US', %s)", value)
        return value

    def _get_conditions(self, field, skip_null=True):
        """The WHERE conditions selecting the rows to overwrite. Flushes first:
        pending ORM writes would otherwise be flushed after the UPDATE and
        overwrite the anonymized values."""
        self.env.flush_all()
        table = SQL.identifier(self._get_model(field)._table)
        conditions = [SQL("%s.id IN %s", table, self._get_query(field).subselect())]
        if skip_null:
            conditions.append(
                SQL("%s.%s IS NOT NULL", table, SQL.identifier(field.field_name))
            )
        return conditions
