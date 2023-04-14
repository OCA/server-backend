# Copyright 2016 LasLabs Inc.

from unittest import mock

from odoo.tests import common

ADAPTER = (
    "odoo.addons.base_external_dbsource_sqlite.models" ".base_external_dbsource.sqlite"
)


class TestBaseExternalDbsource(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.dbsource = self.env.ref("base_external_dbsource_sqlite.demo_sqlite")

    def test_connection_close_sqlalchemy(self):
        """It should close the connection"""
        connection = mock.MagicMock()
        res = self.dbsource._connection_close_sqlalchemy(connection)
        self.assertEqual(res, connection.close())

    def test_connection_open_sqlalchemy(self):
        """It should call SQLAlchemy open"""
        with mock.patch.object(
            type(self.dbsource), "_connection_open_sqlalchemy"
        ) as parent_method:
            self.dbsource._connection_open_sqlalchemy()
            parent_method.assert_called_once_with()

    def test_excecute_sqlalchemy(self):
        """It should pass args to SQLAlchemy execute"""
        expect = "sqlquery", "sqlparams", "metadata"
        with mock.patch.object(
            type(self.dbsource), "_execute_sqlalchemy"
        ) as parent_method:
            self.dbsource._execute_sqlalchemy(*expect)
            parent_method.assert_called_once_with(*expect)

    def test_execute_sqlit_without_sqlparams(self):
        """It should pass args to SQLAlchemy execute"""
        expect = "sqlquery", None, "metadata"
        with mock.patch.object(
            type(self.dbsource), "_execute_sqlalchemy"
        ) as parent_method:
            self.dbsource._execute_sqlalchemy(*expect)
            parent_method.assert_called_once_with(*expect)
