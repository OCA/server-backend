# Copyright 2025 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import logging

import duckdb

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a DuckDB data source using the native SDK."""

    _inherit = "base.external.dbsource"

    connector = fields.Selection(
        selection_add=[("duckdb", "DuckDB")], ondelete={"duckdb": "cascade"}
    )

    readonly = fields.Boolean(default=False)
    config = fields.Json(default={"threads": 1})
    config_display = fields.Text(
        compute="_compute_config_display", inverse="_inverse_config_display"
    )

    @api.depends("config")
    def _compute_config_display(self):
        for rec in self:
            rec.config_display = (
                json.dumps(rec.config, sort_keys=True, indent=4) if rec.config else "{}"
            )

    def _inverse_config_display(self):
        for rec in self:
            rec.config = json.loads(rec.config_display) or {}

    def connection_close_duckdb(self, connection):
        return connection.close()

    def connection_open_duckdb(self):
        db_path = self.conn_string if self.conn_string else ":memory:"
        try:
            conn = duckdb.connect(
                database=db_path, read_only=self.readonly, config=self.config
            )
            return conn
        except Exception as e:
            _logger.error("DuckDB Connection Error: %s", e)
            raise

    def execute_duckdb(self, sqlquery, sqlparams, metadata):
        rows, cols = list(), list()
        for record in self:
            con = record.connection_open_duckdb()
            try:
                cur = con.cursor()
                if sqlparams:
                    cur.execute(sqlquery, sqlparams)
                else:
                    cur.execute(sqlquery)
                if metadata and cur.description:
                    cols = [desc[0] for desc in cur.description]
                if cur.description:
                    rows = cur.fetchall()

            except Exception as e:
                _logger.error("DuckDB Execution Error: %s", e)
                raise
            finally:
                record.connection_close_duckdb(con)
        return rows, cols
