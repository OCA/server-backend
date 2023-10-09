# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import sqlalchemy

from odoo import fields, models


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a SQLite data source."""

    _inherit = "base.external.dbsource"

    PWD_STRING_SQLITE = "Password=%s;"
    connector = fields.Selection(
        selection_add=[("sqlite", "SQLite")], ondelete={"sqlite": "cascade"}
    )

    def connection_close_sqlite(self, connection):
        return connection.close()

    def connection_open_sqlite(self):
        return self._connection_open_sqlalchemy()

    def execute_sqlite(self, sqlquery, sqlparams, metadata):
        return self._execute_sqlalchemy(sqlquery, sqlparams, metadata)

    def _connection_open_sqlalchemy(self):
        return sqlalchemy.create_engine(self.conn_string_full).connect()

    def _execute_sqlalchemy(self, sqlquery, sqlparams, metadata):
        rows, cols = list(), list()
        for record in self:
            with record.connection_open() as connection:
                if sqlparams is None:
                    cur = connection.execute(sqlquery)
                else:
                    cur = connection.execute(sqlquery, sqlparams)
                if metadata:
                    cols = list(cur.keys())
                # If the query doesn't return rows, trying to get them anyway
                # will raise an exception `sqlalchemy.exc.ResourceClosedError`
                rows = [r for r in cur] if cur.returns_rows else []
        return rows, cols
