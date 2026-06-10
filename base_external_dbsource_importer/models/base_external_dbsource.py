# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
import string
from collections import namedtuple
from queue import Queue
from threading import Event, Thread

import xlrd
from psycopg2.extras import RealDictCursor
from sqlalchemy import text

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import ormcache

_logger = logging.getLogger(__name__)

LETTERS = {ord(d): str(i) for i, d in enumerate(string.digits + string.ascii_uppercase)}
BackgroundFetch = namedtuple("BackgroundFetch", ["queue", "killswitch", "thread"])


class BaseExternalModelImporter:
    _name = "base.external.model.importer"
    _external_key = None
    _mapped_model = None

    def __init__(self, dbsource, file_path="", file_name=""):
        self.env = dbsource.env
        self.dbsource: BaseExternalDbsource = dbsource
        self.file_path = file_path
        self.file_name = file_name

    def execute_query(self, sql, params, metadata):
        return True

    def _get_external_records(self, table_name, fields="*", where=""):
        sql = f"SELECT {fields} FROM {table_name} {where};"
        rows, cols = self.execute_query(text(sql), [], metadata=True)
        return rows

    def _get_external_records_from_file(self):
        """Return the same structure of db query but from a file.
        To be implemented by other modules
        """
        return {}

    def load_data(
        self,
        model_name,
        table_name,
        fields="*",
        where="",
        odoo_key="",
        load_all_odoo_records=False,
        origin=False,
    ):
        if not origin:
            fds_records = self._get_external_records(
                table_name, fields=fields, where=where
            )
        else:
            fds_records = self._get_external_records_from_file()
        odoo_key = odoo_key or self._external_key
        records, records_dic = self.load_odoo_records(
            model_name, odoo_key, load_all_odoo_records
        )
        return fds_records, records, records_dic

    def load_odoo_records(self, model_name, odoo_key=None, load_all=False):
        return self.dbsource.load_odoo_records(
            model_name, odoo_key or self._external_key, load_all
        )

    def upsert(
        self,
        fds_key,
        records,
        records_dic,
        vals,
        update_vals=False,
        update_method=True,
        specific_record=None,
        only_update=False,
        force_update=False,
    ):
        force_update = force_update or self.dbsource.force_update
        model_name = records._name
        record = specific_record or records.browse(records_dic.get(fds_key, False))
        if record:
            if not update_method:
                return record
            # Performance issue
            # record = records.filtered(lambda x: x.id == record_id)
            values = (update_vals or vals).copy()
            if not force_update:
                for k, v in values.copy().items():
                    if self.dbsource.skip_update_field(model_name, k) or (
                        record._fields[k].convert_to_write(record[k], record) == v
                    ):
                        values.pop(k)
            if values:
                record.with_context(tracking_disable=True).write(values)
        else:
            Model = self.env[model_name]
            if only_update:
                return Model.browse()
            record = Model.with_context(tracking_disable=True).create(vals)
            records_dic[fds_key] = record.id
        return record

    def get_m2_odoo_id(
        self,
        model_name,
        key_value,
        field_key=False,
        mapped_model=False,
        return_field="id",
    ):
        return self.dbsource.get_m2_odoo_id(
            model_name,
            key_value,
            field_key or self._external_key,
            mapped_model or self._mapped_model,
            return_field,
        )

    def with_context(self, *args, **kwargs):
        context = dict(args[0] if args else self.dbsource._context, **kwargs)
        return self.dbsource.with_context(**context)


class BaseExternalDbsource(models.Model):
    """Provides logic for connection to an external data source."""

    _inherit = "base.external.dbsource"

    fields_to_update_ids = fields.One2many(
        comodel_name="base.external.dbsource.fields.update",
        inverse_name="db_source_id",
        string="Fields To Update",
    )
    only_update = fields.Boolean(string="Only update values", default=True)
    force_update = fields.Boolean(string="Force update all values")
    date_from = fields.Date()
    date_to = fields.Date()
    data_mapper_file = fields.Binary(string="Excel file with data mapped")
    data_mapper_filename = fields.Char(
        string="Excel file filename",
    )

    @ormcache("query", "execute_params", "metadata")
    def execute_and_cache(
        self, query=None, execute_params=None, metadata=False, **kwargs
    ):
        """Caches query response, but requires execute_params to be a tuple"""
        return self.execute(query, list(execute_params), metadata, **kwargs)

    def action_clear_cache(self):
        self.env.registry.clear_all_caches()

    @api.model
    @ormcache("model_name", "key_value", "field_key", "mapped_model", "return_field")
    def get_m2_odoo_id(
        self,
        model_name,
        key_value,
        field_key="fds_key",
        mapped_model=False,
        return_field="id",
    ):
        if not key_value:
            return False
        record = self.env[model_name].search_external(
            key_value, field_key, mapped_model
        )
        return record.id if return_field == "id" else record[return_field].id

    def _number_iban(self, iban):
        return (iban[4:] + iban[:4]).translate(LETTERS)

    def generate_iban_check_digits(self, iban):
        number_iban = self._number_iban(iban[:2] + "00" + iban[4:])
        return f"{98 - (int(number_iban) % 97):0>2}"

    @api.model
    @ormcache("self.fields_to_update_ids.field_ids", "model_name", "field_name")
    def skip_update_field(self, model_name, field_name):
        return field_name not in self.fields_to_update_ids.filtered(
            lambda x: x.model_id.model == model_name
        ).mapped("field_ids.name")

    @api.model
    def load_odoo_records(self, model_name, odoo_key, load_all=False):
        Model = self.env[model_name].with_context(
            active_test=False, prefetch_fields=False
        )
        domain = []
        if not load_all:
            domain = [(odoo_key, "!=", False)]
        records = Model.search(domain)
        records_dic = {
            rec[odoo_key]: rec["id"]
            for rec in records.read([odoo_key])
            if rec.get(odoo_key)
        }
        return records, records_dic

    @api.model
    @ormcache("code", "country_code")
    def _state_country_from_zip(self, code=None, country_code=None):
        CityZip = city_zip = self.env["res.city.zip"]
        if code:
            domain = [("name", "=", code)]
            if country_code:
                domain.append(("country_id.code", "=", country_code))
            city_zip = CityZip.search(domain, limit=1)
        country = city_zip.country_id
        if not country and country_code:
            country = self.env["res.country"].search(
                [("code", "=", country_code)], limit=1
            )
        return (
            city_zip.city_id.state_id.id,
            country.id,
            country.code,
            city_zip.id,
            city_zip.city_id.id,
        )

    def _validate_vat(self, vals, country_code):
        ResPartner = self.env["res.partner"]
        original_vat = vals.pop("vat", "") or ""
        vat = original_vat
        # Clean vat
        vat = (
            vat.replace("-", "")
            .replace(".", "")
            .replace(" ", "")
            .replace("*", "")
            .upper()
        )
        if not vat:
            return vals
        if not vat[1:2].isnumeric():
            country_code, vat = ResPartner._split_vat(vat)
        if not country_code:
            country_code = "ES"
        full_vat = f"{country_code.upper()}{vat}"
        if ResPartner.simple_vat_check(country_code.lower(), vat):
            vals["vat"] = full_vat
        else:
            if vals.get("comment", False):
                vals["comment"] += f"\nVAT: {original_vat}"
            else:
                vals["comment"] = f"VAT: {original_vat}"
        return vals

    def generate_data_mapped_from_file(self, sheet_dic):
        """
        param:
        sheet_dic: Dictionary type {'sheet_name': {
                                        'odoo_col': 1,
                                        'source_col': 2,
                                    }}
        """
        if not self.data_mapper_file:
            raise UserError(self.env._("Debe seleccionar un archivo para importar"))
        xl_workbook = xlrd.open_workbook(
            file_contents=base64.b64decode(self.data_mapper_file)
        )
        data_dic = {}
        for sheet_name, cols_dic in sheet_dic.items():
            xl_sheet = xl_workbook.sheet_by_name(sheet_name)
            odoo_col = cols_dic["odoo_col"]
            source_col = cols_dic["source_col"]
            data_dic[sheet_name] = {}
            for row_idx in range(1, xl_sheet.nrows):
                if xl_sheet.cell_type(row_idx, source_col) == xlrd.XL_CELL_EMPTY:
                    continue
                odoo_ref = xl_sheet.cell(row_idx, odoo_col).value
                if xl_sheet.cell_type(row_idx, source_col) != xlrd.XL_CELL_TEXT:
                    vila_code = str(int(xl_sheet.cell(row_idx, 2).value))
                else:
                    vila_code = xl_sheet.cell(row_idx, source_col).value
                if xl_sheet.cell_type(row_idx, odoo_col) != xlrd.XL_CELL_TEXT:
                    odoo_external = False
                else:
                    odoo_external = self.env.ref(odoo_ref, raise_if_not_found=False)
                data_dic[sheet_name][vila_code] = odoo_external
        return data_dic

    def server_side_cursor_mysql(self, table, fields_sql, where, size=2000):
        with self.connection_open() as conn:
            query = text(f"SELECT {fields_sql} FROM {table} {where}")
            result = conn.execution_options(
                stream_results=True,
                max_row_buffer=size,
            ).execute(query)
            for row in result:
                yield dict(row._mapping)

    def server_side_cursor_postgresql(self, table, fields, where, size=2000):
        # Opens a server side cursor to stream the content of the table in batches
        with self.connection_open() as conn:
            with conn.cursor(
                name="odoo_import", cursor_factory=RealDictCursor
            ) as cursor:
                cursor.itersize = size
                query = f"SELECT {fields} FROM {table} {where} ;"
                cursor.execute(query)
                yield from cursor

    def server_side_cursor(self, table, fields, where, size=2000):
        # To be overwriten in downstream modules
        method = self._get_adapter_method("server_side_cursor")
        yield from method(table, fields, where, size)

    def background_server_cursor(
        self,
        table,
        field,
        where,
        killswitch,
        queue,
        size=2000,
    ):
        gen = self.server_side_cursor(table, field, where, size)
        try:
            for row in gen:
                if killswitch.is_set():
                    break
                queue.put(row)
            queue.put(None)
        except Exception as e:
            queue.put({"_fetch_error": e})
        finally:
            gen.close()

    def background_fetch(self, table, fields, where, size=2000):
        queue = Queue()
        killswitch = Event()
        fetch_thread = Thread(
            target=self.background_server_cursor,
            args=(table, fields, where, killswitch, queue, size),
        )
        _logger.info("Starting fetch thread...")
        fetch_thread.start()
        return BackgroundFetch(queue, killswitch, fetch_thread)

    def queue_iterator(self, queue):
        while True:
            row = queue.get()
            if row is None:
                yield None
                break
            if "_fetch_error" in row:
                raise row["_fetch_error"]
            yield row

    def background_fetch_iterator(self, fecht_data: BackgroundFetch):
        queue, killswitch, fetch_thread = fecht_data
        try:
            yield from self.queue_iterator(queue)
        except Exception as e:
            killswitch.set()
            _logger.critical(f"Error on process thread: {e}")
            raise e
        finally:
            killswitch.set()
            fetch_thread.join()


class DbSourceFieldsUpdate(models.Model):
    _name = "base.external.dbsource.fields.update"
    _description = "Base External Dbsource Fields To Update"

    db_source_id = fields.Many2one(
        comodel_name="base.external.dbsource", string="External Db Source"
    )
    model_id = fields.Many2one(comodel_name="ir.model", string="Model")
    field_ids = fields.Many2many(
        comodel_name="ir.model.fields", string="Fields To Update"
    )
