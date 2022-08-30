# Copyright 2016 LasLabs Inc.

from unittest import mock

from odoo.sql_db import connection_info_for
from odoo.tests import common


class TestBaseExternalDbsource(common.TransactionCase):
    def setUp(self):
        super(TestBaseExternalDbsource, self).setUp()
        # Obtain current odoo instance DB connection settings
        connection_info = connection_info_for(self.env.cr.dbname)[1]
        # Adapt to the format expected by this module
        password = connection_info.get("password", "")
        connection_info["password"] = "%s"
        connection_info["dbname"] = connection_info["database"]
        del connection_info["database"]
        # Create a proper dbsource record to test
        self.dbsource = self.env["base.external.dbsource"].create(
            {
                "conn_string": " ".join(
                    "%s='%s'" % item for item in connection_info.items()
                ),
                "connector": "postgresql",
                "name": "test postgres with current odoo config",
                "password": password,
            }
        )

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
        adapter = "%s_postgresql" % method_name
        with mock.patch.object(type(self.dbsource), adapter, create=create) as adapter:
            if side_effect is not None:
                adapter.side_effect = side_effect
            elif return_value is not None:
                adapter.return_value = return_value
            res = getattr(self.dbsource, method_name)(*args, **kwargs)
            return res, adapter

    def test_conn_string_full(self):
        """It should add password if string interpolation not detected"""
        self.dbsource.conn_string = "User=Derp;"
        self.dbsource.password = "password"
        expect = self.dbsource.conn_string + "PWD=%s;" % self.dbsource.password
        self.assertEqual(self.dbsource.conn_string_full, expect)

    # Interface

    def test_execute_asserts_query_arg(self):
        """It should raise a TypeError if query and sqlquery not in args"""
        with self.assertRaises(TypeError):
            self.dbsource.execute()

    def test_execute_calls_adapter(self):
        """It should call the adapter methods with proper args"""
        expect = ("query", "execute", "metadata")
        return_value = "rows", "cols"
        res, adapter = self._test_adapter_method(
            "execute", args=expect, return_value=return_value
        )
        adapter.assert_called_once_with(*expect)

    def test_execute_return(self):
        """It should return rows if not metadata"""
        expect = (True, True, False)
        return_value = "rows", "cols"
        res, adapter = self._test_adapter_method(
            "execute", args=expect, return_value=return_value
        )
        self.assertEqual(res, return_value[0])

    def test_execute_return_metadata(self):
        """It should return rows and cols if metadata"""
        expect = (True, True, True)
        return_value = "rows", "cols"
        res, adapter = self._test_adapter_method(
            "execute", args=expect, return_value=return_value
        )
        self.assertEqual(res, {"rows": return_value[0], "cols": return_value[1]})

    def test_remote_browse(self):
        """It should call the adapter method with proper args"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = "table"
        res, adapter = self._test_adapter_method(
            "remote_browse", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_browse_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = False
        with self.assertRaises(AssertionError):
            res, adapter = self._test_adapter_method(
                "remote_browse", create=True, args=args, kwargs=kwargs
            )

    def test_remote_create(self):
        """It should call the adapter method with proper args"""
        args = {"val": "Value"}, "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = "table"
        res, adapter = self._test_adapter_method(
            "remote_create", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_create_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = False
        with self.assertRaises(AssertionError):
            res, adapter = self._test_adapter_method(
                "remote_create", create=True, args=args, kwargs=kwargs
            )

    def test_remote_delete(self):
        """It should call the adapter method with proper args"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = "table"
        res, adapter = self._test_adapter_method(
            "remote_delete", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_delete_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = False
        with self.assertRaises(AssertionError):
            res, adapter = self._test_adapter_method(
                "remote_delete", create=True, args=args, kwargs=kwargs
            )

    def test_remote_search(self):
        """It should call the adapter method with proper args"""
        args = {"search": "query"}, "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = "table"
        res, adapter = self._test_adapter_method(
            "remote_search", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_search_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = False
        with self.assertRaises(AssertionError):
            res, adapter = self._test_adapter_method(
                "remote_search", create=True, args=args, kwargs=kwargs
            )

    def test_remote_update(self):
        """It should call the adapter method with proper args"""
        args = [1], {"vals": "Value"}, "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = "table"
        res, adapter = self._test_adapter_method(
            "remote_update", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_update_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        type(self.dbsource).current_table = False
        with self.assertRaises(AssertionError):
            res, adapter = self._test_adapter_method(
                "remote_update", create=True, args=args, kwargs=kwargs
            )

    # Postgres

    def test_execute_postgresql(self):
        """It should call generic executor with proper args"""
        expect = ("query", "execute", "metadata")
        with mock.patch.object(
            type(self.dbsource),
            "_execute_generic",
        ) as execute:
            execute.return_value = "rows", "cols"
            self.dbsource.execute(*expect)
            execute.assert_called_once_with(*expect)

    # Old API Compat

    def test_execute_calls_adapter_old_api(self):
        """It should call the adapter correctly if old kwargs provided"""
        expect = [None, None, "metadata"]
        with mock.patch.object(
            type(self.dbsource),
            "execute_postgresql",
        ) as psql:
            psql.return_value = "rows", "cols"
            self.dbsource.execute(*expect, sqlparams="params", sqlquery="query")
            expect[0], expect[1] = "query", "params"
            psql.assert_called_once_with(*expect)

    def test_conn_open(self):
        """It should return open connection for use"""
        with mock.patch.object(type(self.dbsource), "connection_open") as connection:
            res = self.dbsource.conn_open()
            self.assertEqual(res, connection().__enter__())
