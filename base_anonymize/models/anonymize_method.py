# Copyright 2025 Hunki Enterprises BV
# Copyright 2026 Globalist Technology SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging

from odoo import models
from odoo.tools import SQL

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
        if check_stored and not self._is_stored(field):
            _logger.warning(
                "%s.%s is not stored, %s skips it",
                field.model_name,
                field.field_name,
                self._name,
            )
            return 0
        model = self._get_model(field)
        model_field = model._fields[field.field_name]
        table = SQL.identifier(model._table)
        column = SQL.identifier(field.field_name)
        # pending ORM writes would otherwise be flushed after this UPDATE and
        # overwrite the anonymized values
        self.env.flush_all()
        if getattr(model_field, "translate", False):
            value = SQL("jsonb_build_object('en_US', %s)", value)
        conditions = [SQL("%s.id IN %s", table, self._get_query(field).subselect())]
        if skip_null:
            conditions.append(SQL("%s.%s IS NOT NULL", table, column))
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
