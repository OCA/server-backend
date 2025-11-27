# Copyright (C) 2025 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import common

ADAPTER = (
    "odoo.addons.base_external_dbsource_mssql_by_odbc.models"
    ".base_external_dbsource.pymssql"
)


class TestBaseExternalDbsource(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbsource = cls.env.ref(
            "base_external_dbsource_mssql_by_odbc.demo_mssql_pyodbc"
        )

    def test_connection_close_mssql_pyodbc(self):
        """It should close the connection"""
        connection = mock.MagicMock()
        res = self.dbsource.connection_close_mssql_pyodbc(connection)
        self.assertEqual(res, connection.close())

    def test_connection_open_mssql_pyodbc(self):
        """It should call PyODBC open"""
        with mock.patch.object(
            type(self.dbsource), "_connection_open_mssql_pyodbc"
        ) as parent_method:
            self.dbsource.connection_open_mssql_pyodbc()
            parent_method.assert_called_once_with()

    def test_excecute_mssql_pyodbc(self):
        """It should pass args to PyODBC execute"""
        expect = "sqlquery", "sqlparams", "metadata"
        with mock.patch.object(
            type(self.dbsource), "_execute_mssql_pyodbc"
        ) as parent_method:
            self.dbsource.execute_mssql_pyodbc(*expect)
            parent_method.assert_called_once_with(*expect)
