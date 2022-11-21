# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import pymssql

from odoo import models

from odoo.addons.base_external_dbsource.models import base_external_dbsource

CONNECTORS = base_external_dbsource.BaseExternalDbsource.CONNECTORS
CONNECTORS.append(("mssql", "Microsoft SQL Server"))

assert pymssql


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a MSSQL data source."""

    _inherit = "base.external.dbsource"

    PWD_STRING_MSSQL = "Password=%s;"

    def connection_close_mssql(self, connection):
        return connection.close()

    def connection_open_mssql(self):
        return self._connection_open_sqlalchemy()

    def execute_mssql(self, sqlquery, sqlparams, metadata):
        return self._execute_sqlalchemy(sqlquery, sqlparams, metadata)
