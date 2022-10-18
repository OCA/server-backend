# Copyright 2022 Tecnativa - Sergio Teruel
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from odoo.tests import common

ADAPTER = "odoo.addons.base_external_dbsource_sap_hana.models.base_external_dbsource.SAPhanaDB"


class TestBaseExternalDbsource(common.TransactionCase):
    def setUp(self):
        super(TestBaseExternalDbsource, self).setUp()
        self.dbsource = self.env.ref("base_external_dbsource_sap_hana.demo_sap_hana")

    def _test_adapter_method(
        self,
        method_name,
        side_effect=None,
        return_value=None,
        create=False,
        args=None,
        kwargs=None,
    ):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        adapter = "%s_sap_hana" % method_name
        with mock.patch.object(type(self.dbsource), adapter, create=create) as adapter:
            if side_effect is not None:
                adapter.side_effect = side_effect
            elif return_value is not None:
                adapter.return_value = return_value
            res = getattr(self.dbsource, method_name)(*args, **kwargs)
            return res, adapter

    def test_connection_close_sap_hana(self):
        """It should close the connection"""
        args = [mock.MagicMock()]
        res, adapter = self._test_adapter_method("connection_close", args=args)
        adapter.assert_called_once_with(args[0])

    def test_connection_open_sap_hana(self):
        """It should call SQLAlchemy open"""
        with mock.patch.object(type(self.dbsource), "connection_open") as connection:
            res = self.dbsource.conn_open()
            self.assertEqual(res, connection().__enter__())

    def test_excecute_sap_hana(self):
        """It should pass args to SQLAlchemy execute"""
        expect = "sqlquery", "sqlparams", "metadata"
        with mock.patch.object(type(self.dbsource), "execute_sap_hana") as execute:
            execute.return_value = "rows", "cols"
            self.dbsource.execute(*expect)
            execute.assert_called_once_with(*expect)
