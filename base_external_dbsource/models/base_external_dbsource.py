# Copyright 2011 Daniel Reis
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging
from contextlib import contextmanager

import psycopg2

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to an external data source

    Classes implementing this interface must provide the following methods
    suffixed with the adapter type. See the method definitions and examples
    for more information:
        * ``connection_open_*``
        * ``connection_close_*``
        * ``execute_*``

    Optional methods for adapters to implement:
        * ``remote_browse_*``
        * ``remote_create_*``
        * ``remote_delete_*``
        * ``remote_search_*``
        * ``remote_update_*``
    """

    _name = "base.external.dbsource"
    _description = "External Database Sources"

    name = fields.Char("Datasource name", required=True)
    conn_string = fields.Text(
        "Connection string",
        help="""
    Sample connection strings ("%s" will be replaced by the password):
    - Microsoft SQL Server:
      mssql+pymssql://username:%s@server:port/dbname?charset=utf8
    - MySQL: mysql://user:%s@server:port/dbname
    - ODBC: DRIVER={FreeTDS};SERVER=server.address;Database=mydb;UID=sa
    - ORACLE: username/%s@//server.address:port/instance
    - PostgreSQL:
        dbname='template1' user='dbuser' host='localhost' port='5432' \
        password=%s
    - SQLite: sqlite:///test.db
    - Elasticsearch: https://user:%s@localhost:9200
    """,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
    )
    conn_string_full = fields.Text(readonly=True, compute="_compute_conn_string_full")
    password = fields.Char()
    client_cert = fields.Text()
    client_key = fields.Text()
    ca_certs = fields.Char(help="Path to CA Certs file on server.")
    connector = fields.Selection(
        [("postgresql", "PostgreSQL")],
        required=True,
        help="If a connector is missing from the list, check the server "
        "log to confirm that the required components were detected.",
    )

    _current_table = None

    @api.depends("conn_string", "password")
    def _compute_conn_string_full(self):
        for record in self:
            try:
                record.conn_string_full = record.conn_string % record.password
            except TypeError:
                record.conn_string_full = record.conn_string

    # Interface

    def _change_table(self, name):
        """Change the table that is used for CRUD operations"""
        self._current_table = name

    def _connection_close(self, connection):
        """It closes the connection to the data source.

        This method calls adapter method of this same name, suffixed with
        the adapter type.
        """

        method = self._get_adapter_method("connection_close")
        return method(connection)

    @contextmanager
    def _connection_open(self):
        """It provides a context manager for the data source.

        This method calls adapter method of this same name, suffixed with
        the adapter type.
        """

        method = self._get_adapter_method("connection_open")
        try:
            connection = method()
            yield connection
        finally:
            try:
                self._connection_close(connection)
            except Exception:
                _logger.exception("Connection close failure.")

    def _execute(self, query, execute_params=None, metadata=False, **kwargs):
        """Executes a query and returns a list of rows.

        "execute_params" can be a dict of values, that can be referenced
        in the SQL statement using "%(key)s" or, in the case of Oracle,
        ":key".
        Example:
            query = "SELECT * FROM mytable WHERE city = %(city)s AND
                        date > %(dt)s"
            execute_params   = {
                'city': 'Lisbon',
                'dt': datetime.datetime(2000, 12, 31),
            }

        If metadata=True, it will instead return a dict containing the
        rows list and the columns list, in the format:
            { 'cols': [ 'col_a', 'col_b', ...]
            , 'rows': [ (a0, b0, ...), (a1, b1, ...), ...] }
        """
        method = self._get_adapter_method("execute")
        rows, cols = method(query, execute_params, metadata)

        if metadata:
            return {"cols": cols, "rows": rows}
        else:
            return rows

    def connection_test(self):
        """It tests the connection

        Raises:
            Validation message with the result of the connection (fail or success)
        """
        try:
            with self._connection_open():
                pass
        except Exception as e:
            raise ValidationError(
                _("Connection test failed:\n" "Here is what we got instead:\n%s")
                % tools.ustr(e)
            ) from e
        raise ValidationError(
            _("Connection test succeeded:\n" "Everything seems properly set up!")
        )

    def _remote_browse(self, record_ids, *args, **kwargs):
        """It browses for and returns the records from remote by ID

        This method calls adapter method of this same name, suffixed with
        the adapter type.

        Args:
            record_ids: (list) List of remote IDs to browse.
            *args: Positional arguments to be passed to adapter method.
            **kwargs: Keyword arguments to be passed to adapter method.
        Returns:
            (iter) Iterator of record mappings that match the ID.
        """

        assert self._current_table
        method = self._get_adapter_method("remote_browse")
        return method(record_ids, *args, **kwargs)

    def _remote_create(self, vals, *args, **kwargs):
        """It creates a record on the remote data source.

        This method calls adapter method of this same name, suffixed with
        the adapter type.

        Args:
            vals: (dict) Values to use for creation.
            *args: Positional arguments to be passed to adapter method.
            **kwargs: Keyword arguments to be passed to adapter method.
        Returns:
            (mapping) A mapping of the record that was created.
        """

        assert self._current_table
        method = self._get_adapter_method("remote_create")
        return method(vals, *args, **kwargs)

    def _remote_delete(self, record_ids, *args, **kwargs):
        """It deletes records by ID on remote

        This method calls adapter method of this same name, suffixed with
        the adapter type.

        Args:
            record_ids: (list) List of remote IDs to delete.
            *args: Positional arguments to be passed to adapter method.
            **kwargs: Keyword arguments to be passed to adapter method.
        Returns:
            (iter) Iterator of bools indicating delete status.
        """

        assert self._current_table
        method = self._get_adapter_method("remote_delete")
        return method(record_ids, *args, **kwargs)

    def _remote_search(self, query, *args, **kwargs):
        """It searches the remote for the query.

        This method calls adapter method of this same name, suffixed with
        the adapter type.

        Args:
            query: (mixed) Query domain as required by the adapter.
            *args: Positional arguments to be passed to adapter method.
            **kwargs: Keyword arguments to be passed to adapter method.
        Returns:
            (iter) Iterator of record mappings that match query.
        """

        assert self._current_table
        method = self._get_adapter_method("remote_search")
        return method(query, *args, **kwargs)

    def _remote_update(self, record_ids, vals, *args, **kwargs):
        """It updates the remote records with the vals

        This method calls adapter method of this same name, suffixed with
        the adapter type.

        Args:
            record_ids: (list) List of remote IDs to delete.
            *args: Positional arguments to be passed to adapter method.
            **kwargs: Keyword arguments to be passed to adapter method.
        Returns:
            (iter) Iterator of record mappings that were updated.
        """

        assert self._current_table
        method = self._get_adapter_method("remote_update")
        return method(record_ids, vals, *args, **kwargs)

    # Adapters

    def _connection_close_postgresql(self, connection):
        return connection.close()

    def _connection_open_postgresql(self):
        return psycopg2.connect(self.conn_string_full)

    def _execute_postgresql(self, query, params, metadata):
        return self._execute_generic(query, params, metadata)

    def _execute_generic(self, query, params, metadata):
        with self._connection_open() as connection:
            cur = connection.cursor()
            cur.execute(query, params)
            cols = []
            if metadata:
                cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return rows, cols

    # Compatibility & Private

    def _get_adapter_method(self, method_prefix):
        """It returns the connector adapter method for ``method_prefix``.

        Args:
            method_prefix: (str) Prefix of adapter method (such as
                ``connection_open``).
        Raises:
            NotImplementedError: When the method is not found
        Returns:
            (instancemethod)
        """

        self.ensure_one()
        method = "_{}_{}".format(method_prefix, self.connector)

        try:
            return getattr(self, method)
        except AttributeError:
            raise NotImplementedError(
                _(
                    '"%(method)s" method not found, check that all assets are installed '
                    "for the %(connector)s connector type.",
                    method=method,
                    conector=self.connector,
                )
            ) from AttributeError
