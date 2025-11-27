# Copyright (C) 2025 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pyodbc

from odoo import fields, models


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a MSSQL data source."""

    _inherit = "base.external.dbsource"

    connector = fields.Selection(
        selection_add=[("mssql_pyodbc", "Microsoft SQL Server (PyODBC)")],
        ondelete={"mssql_pyodbc": "cascade"},
    )
    PWD_STRING_MSSQL_PYODBC = "Password=%s;"

    def connection_close_mssql_pyodbc(self, connection):
        return connection.close()

    def connection_open_mssql_pyodbc(self):
        return self._connection_open_mssql_pyodbc()

    def execute_mssql_pyodbc(self, sqlquery, sqlparams, metadata):
        return self._execute_mssql_pyodbc(sqlquery, sqlparams, metadata)

    def _connection_open_mssql_pyodbc(self):
        return pyodbc.connect(self.conn_string_full)

    def _execute_mssql_pyodbc(self, sqlquery, sqlparams, metadata):
        rows, cols = list(), list()
        for record in self:
            with record.connection_open() as connection:
                cursor = connection.cursor()
                if sqlparams is None:
                    cursor.execute(sqlquery)
                else:
                    cursor.execute(sqlquery, sqlparams)
                if metadata:
                    cols = [column[0] for column in cursor.description]
                if (
                    cursor.description
                ):  # description is only set for queries that return data
                    rows = cursor.fetchall()
                else:
                    rows = list()
        return rows, cols
