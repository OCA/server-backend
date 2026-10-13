# Copyright 2022 Tecnativa - Sergio Teruel
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


import sqlalchemy

from odoo import fields, models


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a SAP Hana data source."""

    _inherit = "base.external.dbsource"

    connector = fields.Selection(
        selection_add=[("sap_hana", "SAP-Hana")],
        ondelete={"sap_hana": "cascade"},
    )

    def connection_close_sap_hana(self, connection):
        return connection.close()

    def connection_open_sap_hana(self):
        return sqlalchemy.create_engine(self.conn_string_full).connect()

    def execute_sap_hana(self, sqlquery, sqlparams, metadata):
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
