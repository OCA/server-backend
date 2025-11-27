# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# Copyright 2025 Abraham Anes
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import fdb

from odoo import fields, models


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to an Firebird data source."""

    _inherit = "base.external.dbsource"

    PWD_STRING_FDB = "Password=%s;"
    connector = fields.Selection(
        selection_add=[("fdb", "Firebird")], ondelete={"fdb": "cascade"}
    )

    def connection_close_fdb(self, connection):
        return connection.close()

    def connection_open_fdb(self):
        kwargs = {}
        for option in self.conn_string_full.split(";"):
            try:
                key, value = option.split("=")
            except ValueError:
                continue
            kwargs[key.lower()] = value
        return fdb.connect(**kwargs)

    def execute_fdb(self, sqlquery, sqlparams, metadata):
        with self.connection_open_fdb() as conn:
            cur = conn.cursor()
            if sqlparams is None:
                cur.execute(sqlquery)
            else:
                cur.execute(sqlquery, sqlparams)
            rows = cur.fetchall()
            return rows, []
