# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import sqlalchemy

from odoo import fields, models


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a SQLAlchemy data source."""

    _inherit = "base.external.dbsource"

    connector = fields.Selection(
        selection_add=[("sqlalchemy", "SQLAlchemy")], ondelete={"sqlalchemy": "cascade"}
    )

    def _connection_close_sqlalchemy(self, connection):
        return connection.close()

    def _connection_open_sqlalchemy(self):
        return sqlalchemy.create_engine(self.conn_string_full).connect()

    def _execute_sqlalchemy(self, sqlquery, sqlparams, metadata):
        rows, cols = list(), list()
        for record in self:
            with record.connection_open() as connection:
                if sqlparams is None:
                    cur = connection.execute(sqlquery)
                else:
                    cur = connection.execute(sqlquery, sqlparams)
                if metadata:
                    cols = list(cur.keys())
                rows = [r for r in cur]
        return rows, cols
