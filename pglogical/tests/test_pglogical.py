# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mock
from contextlib import contextmanager
from odoo.sql_db import Cursor
from odoo.tests.common import TransactionCase
from odoo.tools.config import config
from ..hooks import post_load


class TestPglogical(TransactionCase):
    @contextmanager
    def _config(self, misc, test_enable=False):
        """
        Temporarily change the config to test_enable=False and impose a custom misc
        section
        """
        original_misc = config.misc
        config.misc = misc
        config["test_enable"] = test_enable
        yield
        config["test_enable"] = True
        config.misc = original_misc

    def test_configuration(self):
        """Test we react correctly to misconfigurations"""
        with self._config(
            dict(pglogical=dict(replication_sets="nothing")), True
        ), self.assertLogs("odoo.addons.pglogical") as log:
            post_load()
        self.assertEqual(
            log.output,
            ["INFO:odoo.addons.pglogical:test mode enabled, not doing anything"],
        )

        with self._config({}), self.assertLogs("odoo.addons.pglogical") as log:
            post_load()

        self.assertEqual(
            log.output,
            [
                "INFO:odoo.addons.pglogical:pglogical section missing in config, "
                "not doing anything"
            ],
        )

        with self._config(dict(pglogical={"hello": "world"})), self.assertLogs(
            "odoo.addons.pglogical"
        ) as log:
            post_load()

        self.assertEqual(
            log.output,
            [
                "ERROR:odoo.addons.pglogical:no replication sets defined, "
                "not doing anything"
            ],
        )

    def test_patching(self):
        """Test patching the cursor succeeds"""
        with self._config(dict(pglogical=dict(replication_sets="set1,set2"))):
            try:
                post_load()
                self.assertTrue(getattr(Cursor.execute, "origin", False))
                with mock.patch.object(self.env.cr, "_obj") as mock_cursor:
                    self.env.cr.execute("ALTER TABLE test ADD COLUMN test varchar")
                self.assertIn(
                    "pglogical.replicate_ddl_command",
                    mock_cursor.execute.call_args[0][0],
                )

                with mock.patch.object(self.env.cr, "_obj") as mock_cursor:
                    self.env.cr.execute(
                        "ALTER TABLE test ADD CONSTRAINT test unique(id)"
                    )

                self.assertNotIn(
                    "pglogical.replicate_ddl_command",
                    mock_cursor.execute.call_args[0][0],
                )

                with mock.patch.object(self.env.cr, "_obj") as mock_cursor:
                    self.env.cr.execute("SELECT * from test")

                self.assertNotIn(
                    "pglogical.replicate_ddl_command",
                    mock_cursor.execute.call_args[0][0],
                )
            finally:
                Cursor.execute = getattr(Cursor.execute, "origin", Cursor.execute)
