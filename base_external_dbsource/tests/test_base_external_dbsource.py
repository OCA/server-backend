# Copyright 2016 LasLabs Inc.

from contextlib import contextmanager
from unittest import mock

from odoo.exceptions import AccessError, ValidationError
from odoo.sql_db import connection_info_for
from odoo.tests import common


class TestBaseExternalDbsource(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Obtain current odoo instance DB connection settings
        connection_info = connection_info_for(cls.env.cr.dbname)[1]
        # Adapt to the format expected by this module
        password = connection_info.get("password", "")
        connection_info["password"] = "%s"
        connection_info["dbname"] = connection_info["database"]
        del connection_info["database"]
        # Create a proper dbsource record to test
        cls.dbsource = cls.env["base.external.dbsource"].create(
            {
                "conn_string": " ".join(
                    f"{key}='{value}'" for key, value in connection_info.items()
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
        adapter = f"{method_name}_postgresql"
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
        expect = f"{self.dbsource.conn_string}PWD={self.dbsource.password};"
        self.assertEqual(self.dbsource.conn_string_full, expect)

        self.dbsource.conn_string = "User=Derp;"
        self.dbsource.password = ""
        expect = self.dbsource.conn_string
        self.assertEqual(self.dbsource.conn_string_full, expect)

        self.dbsource.conn_string = "User=Derp;PWD=%s;"
        self.dbsource.password = "password"
        expect = self.dbsource.conn_string % self.dbsource.password
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
        _res, adapter = self._test_adapter_method(
            "execute", args=expect, return_value=return_value
        )
        adapter.assert_called_once_with(*expect)

    def test_execute_return(self):
        """It should return rows if not metadata"""
        expect = (True, True, False)
        return_value = "rows", "cols"
        res, _adapter = self._test_adapter_method(
            "execute", args=expect, return_value=return_value
        )
        self.assertEqual(res, return_value[0])

    def test_execute_return_metadata(self):
        """It should return rows and cols if metadata"""
        expect = (True, True, True)
        return_value = "rows", "cols"
        res, _adapter = self._test_adapter_method(
            "execute", args=expect, return_value=return_value
        )
        self.assertEqual(res, {"rows": return_value[0], "cols": return_value[1]})

    def test_remote_browse(self):
        """It should call the adapter method with proper args"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource.change_table("table")
        res, adapter = self._test_adapter_method(
            "remote_browse", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_browse_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource._current_table_by_id.pop(self.dbsource.id, None)
        with self.assertRaises(AssertionError):
            self._test_adapter_method(
                "remote_browse", create=True, args=args, kwargs=kwargs
            )

    def test_remote_create(self):
        """It should call the adapter method with proper args"""
        args = {"val": "Value"}, "args"
        kwargs = {"kwargs": True}
        self.dbsource.change_table("table")
        res, adapter = self._test_adapter_method(
            "remote_create", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_create_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource._current_table_by_id.pop(self.dbsource.id, None)
        with self.assertRaises(AssertionError):
            self._test_adapter_method(
                "remote_create", create=True, args=args, kwargs=kwargs
            )

    def test_remote_delete(self):
        """It should call the adapter method with proper args"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource.change_table("table")
        res, adapter = self._test_adapter_method(
            "remote_delete", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_delete_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource._current_table_by_id.pop(self.dbsource.id, None)
        with self.assertRaises(AssertionError):
            self._test_adapter_method(
                "remote_delete", create=True, args=args, kwargs=kwargs
            )

    def test_remote_search(self):
        """It should call the adapter method with proper args"""
        args = {"search": "query"}, "args"
        kwargs = {"kwargs": True}
        self.dbsource.change_table("table")
        res, adapter = self._test_adapter_method(
            "remote_search", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_search_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource._current_table_by_id.pop(self.dbsource.id, None)
        with self.assertRaises(AssertionError):
            self._test_adapter_method(
                "remote_search", create=True, args=args, kwargs=kwargs
            )

    def test_remote_update(self):
        """It should call the adapter method with proper args"""
        args = [1], {"vals": "Value"}, "args"
        kwargs = {"kwargs": True}
        self.dbsource.change_table("table")
        res, adapter = self._test_adapter_method(
            "remote_update", create=True, args=args, kwargs=kwargs
        )
        adapter.assert_called_once_with(*args, **kwargs)
        self.assertEqual(res, adapter())

    def test_remote_update_asserts_current_table(self):
        """It should raise AssertionError if a table not selected"""
        args = [1], "args"
        kwargs = {"kwargs": True}
        self.dbsource._current_table_by_id.pop(self.dbsource.id, None)
        with self.assertRaises(AssertionError):
            self._test_adapter_method(
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

    def test_connection_close(self):
        """It should call the close method on the connection object"""
        mock_connection = mock.Mock()
        self.dbsource.connection_close(mock_connection)
        mock_connection.close.assert_called_once()

    def test_execute_missing_query_and_params(self):
        """It should raise a TypeError if both query and execute_params are missing"""
        with self.assertRaises(TypeError):
            self.dbsource.execute(metadata=True)

    def test_connection_close_postgresql(self):
        """It should call the close method on the connection object"""
        mock_connection = mock.Mock()
        self.dbsource.connection_close_postgresql(mock_connection)
        mock_connection.close.assert_called_once()

    def test_change_table(self):
        """It should set the current table used for remote CRUD operations"""
        self.dbsource.change_table("res_partner")
        self.assertEqual(self.dbsource.current_table, "res_partner")

    def test_connection_test_success(self):
        """It should raise a success ValidationError when the connection opens"""

        @contextmanager
        def _connection_open_ok(self):
            yield mock.Mock()

        with (
            mock.patch.object(
                type(self.dbsource), "connection_open", _connection_open_ok
            ),
            self.assertRaises(ValidationError) as ctx,
        ):
            self.dbsource.connection_test()
        self.assertIn("Connection test succeeded", str(ctx.exception))

    def test_connection_test_failure(self):
        """It should raise a failure ValidationError when the connection fails"""

        @contextmanager
        def _connection_open_fail(self):
            raise ConnectionError("connection refused")

        with (
            mock.patch.object(
                type(self.dbsource), "connection_open", _connection_open_fail
            ),
            self.assertRaises(ValidationError) as ctx,
        ):
            self.dbsource.connection_test()
        self.assertIn("Connection test failed", str(ctx.exception))
        self.assertIn("connection refused", str(ctx.exception))

    def test_get_adapter_method_not_implemented(self):
        """It should raise NotImplementedError for unknown adapter methods"""
        with self.assertRaises(NotImplementedError) as ctx:
            self.dbsource._get_adapter_method("nonexistent")
        self.assertIn("nonexistent_postgresql", str(ctx.exception))

    def test_connection_open_context_manager(self):
        """It should close the connection when leaving the context manager"""
        mock_connection = mock.Mock()
        with (
            mock.patch.object(
                type(self.dbsource),
                "connection_open_postgresql",
                return_value=mock_connection,
            ),
            mock.patch.object(
                type(self.dbsource), "connection_close_postgresql"
            ) as close_mock,
        ):
            with self.dbsource.connection_open():
                pass
            close_mock.assert_called_once_with(mock_connection)

    def test_conn_string_compute_preserves_source(self):
        self.dbsource.conn_string = "User=Derp;"
        self.dbsource.password = "password"
        self.assertEqual(self.dbsource.conn_string_full, "User=Derp;PWD=password;")
        self.assertEqual(self.dbsource.conn_string, "User=Derp;")
        self.dbsource.password = "replacement"
        self.assertEqual(self.dbsource.conn_string_full, "User=Derp;PWD=replacement;")
        self.assertEqual(self.dbsource.conn_string, "User=Derp;")

    def test_conn_string_empty_with_password(self):
        self.dbsource.conn_string = False
        self.dbsource.password = "password"
        self.assertEqual(self.dbsource.conn_string_full, "PWD=password;")
        self.assertFalse(self.dbsource.conn_string)

    def test_connection_open_failure_does_not_close(self):
        with (
            mock.patch.object(
                type(self.dbsource),
                "connection_open_postgresql",
                side_effect=ConnectionError("connection refused"),
            ),
            mock.patch.object(type(self.dbsource), "connection_close") as close,
        ):
            with (
                self.assertRaisesRegex(ConnectionError, "connection refused"),
                self.dbsource.connection_open(),
            ):
                self.fail("Connection unexpectedly opened")
            close.assert_not_called()

    def test_connection_closes_on_query_failure(self):
        connection = mock.Mock()
        with (
            mock.patch.object(
                type(self.dbsource),
                "connection_open_postgresql",
                return_value=connection,
            ),
            self.assertRaisesRegex(ValueError, "query failed"),
            self.dbsource.connection_open(),
        ):
            raise ValueError("query failed")
        connection.close.assert_called_once_with()

    def test_execute_postgresql_integration(self):
        self.dbsource.conn_string += " connect_timeout=5"
        self.assertEqual(
            self.dbsource.execute("SELECT %s::integer AS value", (42,)), [(42,)]
        )
        self.assertEqual(
            self.dbsource.execute(
                "SELECT %(value)s::integer AS value",
                {"value": 7},
                metadata=True,
            ),
            {"rows": [(7,)], "cols": ["value"]},
        )

    def test_internal_user_cannot_access_sources(self):
        user = common.new_test_user(self.env, login="dbsource_internal")
        with self.assertRaises(AccessError):
            self.dbsource.with_user(user).read(["password"])

    def test_administrator_multicompany_access(self):
        company = self.env.company
        other_company = self.env["res.company"].create({"name": "Other DB company"})
        user = common.new_test_user(
            self.env,
            login="dbsource_admin",
            groups="base.group_system",
            company_id=company.id,
            company_ids=[(6, 0, [company.id, other_company.id])],
        )
        sources = self.env["base.external.dbsource"].create(
            [
                {"name": "Own", "connector": "postgresql", "company_id": company.id},
                {
                    "name": "Other",
                    "connector": "postgresql",
                    "company_id": other_company.id,
                },
                {"name": "Shared", "connector": "postgresql", "company_id": False},
            ]
        )
        allowed = sources.with_user(user).with_context(allowed_company_ids=[company.id])
        self.assertEqual(
            set(allowed.search([("id", "in", sources.ids)]).ids),
            {sources[0].id, sources[2].id},
        )
        with self.assertRaises(AccessError):
            allowed[1].read(["name"])
        with self.assertRaises(AccessError):
            allowed[1].write({"name": "Forbidden"})
        with self.assertRaises(AccessError):
            allowed[1].unlink()
        with self.assertRaises(AccessError), self.cr.savepoint():
            allowed.create(
                {
                    "name": "Forbidden",
                    "connector": "postgresql",
                    "company_id": other_company.id,
                }
            )
        both = allowed.with_context(allowed_company_ids=[company.id, other_company.id])
        self.assertEqual(
            set(both.search([("id", "in", sources.ids)]).ids), set(sources.ids)
        )
