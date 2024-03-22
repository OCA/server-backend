# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import sqlalchemy

from odoo import models

from odoo.addons.base_external_dbsource.models import base_external_dbsource

base_external_dbsource.BaseExternalDbsource.CONNECTORS.append(("mysql", "MySQL"))


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a MySQL data source."""

    _inherit = "base.external.dbsource"

    def connection_close_mysql(self, connection):
        return connection.close()

    def connection_open_mysql(self):
        return sqlalchemy.create_engine(self.conn_string_full).connect()

    def execute_mysql(self, sqlquery, sqlparams, metadata):
        # FIXME: Duplicated method in modules to be consolidated in base
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
