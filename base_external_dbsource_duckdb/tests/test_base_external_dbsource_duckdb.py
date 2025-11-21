# Copyright 2025 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tools import misc, mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestBaseExternalDbsource(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbsource = cls.env["base.external.dbsource"].create(
            {
                "name": "DuckDB in memory",
                "conn_string": ":memory:",
                "connector": "duckdb",
            }
        )
        cls.file_path1 = misc.file_path(
            f"{cls.test_module}/tests/test_files/sample1.csv"
        )
        cls.file_path2 = misc.file_path(
            f"{cls.test_module}/tests/test_files/sample2.json"
        )

    def test_01_duckdb_with_sql_param(self):
        res = self.dbsource.execute(
            f"""
            SELECT s1.name || ' ' || j.value as greeting
            FROM '{self.file_path1}' s1
            JOIN (
                SELECT * FROM read_json_auto('{self.file_path2}')
            ) j ON s1.id = j.id
            WHERE s1.id = ?
        """,
            [1],
        )

        self.assertEqual(res[0][0], "Hello World!")

    def test_02_duckdb_with_sql_param_dict(self):
        res = self.dbsource.execute(
            f"""
            SELECT s1.name || ' ' || j.value as greeting
            FROM '{self.file_path1}' s1
            JOIN (
                SELECT * FROM read_json_auto('{self.file_path2}')
            ) j ON s1.id = j.id
            WHERE s1.id = $id
        """,
            {"id": 1},
        )

        self.assertEqual(res[0][0], "Hello World!")

    def test_03_duckdb_with_metadata(self):
        res = self.dbsource.execute(
            f"""
            SELECT s1.name || ' ' || j.value as test
            FROM '{self.file_path1}' s1
            JOIN (
                SELECT * FROM read_json_auto('{self.file_path2}')
            ) j ON s1.id = j.id
            WHERE s1.id = 2
        """,
            None,
            True,
        )
        self.assertEqual(res, {"cols": ["test"], "rows": [("Test Data",)]})

    @mute_logger(
        "odoo.addons.base_external_dbsource_duckdb.models.base_external_dbsource"
    )
    def test_04_duckdb_with_error_raise(self):
        with self.assertRaises(Exception) as error_catcher:
            self.dbsource.execute(
                f"""
                SELECT s1.name || ' ' || j.value as test
                FROM '{self.file_path1}' s1
                JOIN (
                    SELECT * FROM read_json_auto('{self.file_path2}')
                ) j ON s1.id = j.id
                WHERE s1.id = %s
            """,
                (2,),
                True,
            )
        self.assertTrue(
            error_catcher.exception.args[0].startswith(
                'Parser Error: syntax error at or near "%"'
            )
        )
