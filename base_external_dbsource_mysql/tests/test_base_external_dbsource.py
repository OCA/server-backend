# Copyright 2016 LasLabs Inc.

from unittest import mock

from odoo.tests import common

ADAPTER = (
    "odoo.addons.base_external_dbsource_mysql.models.base_external_dbsource.MySQLdb"
)


class TestBaseExternalDbsource(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbsource = cls.env.ref("base_external_dbsource_mysql.demo_mysql")

    def test_connection_close_mysql(self):
        """It should close the connection"""
        connection = mock.MagicMock()
        res = self.dbsource.connection_close_mysql(connection)
        self.assertEqual(res, connection.close())

    def test_connection_open_mysql(self):
        """It should call SQLAlchemy open"""
        with mock.patch.object(
            type(self.dbsource), "connection_open_mysql"
        ) as parent_method:
            self.dbsource.connection_open_mysql()
            parent_method.assert_called_once_with()

    def test_excecute_mysql(self):
        """It should pass args to SQLAlchemy execute"""
        expect = "sqlquery", "sqlparams", "metadata"
        with mock.patch.object(type(self.dbsource), "execute_mysql") as parent_method:
            self.dbsource.execute_mysql(*expect)
            parent_method.assert_called_once_with(*expect)
