# -*- coding: utf-8 -*-
# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import api
from odoo import models


_logger = logging.getLogger(__name__)

try:
    from odoo.addons.base_external_dbsource.models import (
        base_external_dbsource,
    )
    CONNECTORS = base_external_dbsource.BaseExternalDbsource.CONNECTORS
    try:
        import fdb
        CONNECTORS.append(('fdb', 'Firebird'))
        import pandas as pd
    except:
        _logger.info('Firebird library not available. Please install "fdb and/or pandas" '
                     'python package.')
except ImportError:
    _logger.info('base_external_dbsource Odoo module not found.')


class BaseExternalDbsource(models.Model):
    """ It provides logic for connection to an Firebird data source. """

    _inherit = "base.external.dbsource"

    PWD_STRING_FDB = 'Password=%s;'


    def connection_close_fdb(self, connection):
        self.ensure_one()

        return connection.close()


    def connection_open_fdb(self):
        self.ensure_one()

        kwargs = {}
        for option in self.conn_string_full.split(';'):
            try:
                key, value = option.split('=')
            except ValueError:
                continue
            if key.lower() == "port" :
                kwargs[key.lower()] = int(value)
            else : 
                kwargs[key.lower()] = value
        return fdb.connect(**kwargs)

    def execute_fdb(self, sqlquery, sqlparams):
        self.ensure_one()

        with self.connection_open_fdb() as conn:
            cur = conn.cursor()
            cur.execute(sqlquery % sqlparams)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
        
            # Create a DataFrame from the rows and columns
            df = pd.DataFrame(rows, columns=columns)
            
            return df
