# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
import string

import xlrd
from sqlalchemy import text

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import ormcache

_logger = logging.getLogger(__name__)

LETTERS = {ord(d): str(i) for i, d in enumerate(string.digits + string.ascii_uppercase)}


class BaseExternalModelImporter:
    _name = "base.external.model.importer"
    _external_key = None

    def __init__(self, dbsource, file_path="", file_name=""):
        self.env = dbsource.env
        self.dbsource = dbsource
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
        odoo_key = odoo_key or self._external_key
        Model = self.env[model_name]
        if not origin:
            fds_records = self._get_external_records(
                table_name, fields=fields, where=where
            )
        else:
            fds_records = self._get_external_records_from_file()
        domain = []
        if not load_all_odoo_records:
            domain = [(odoo_key, "!=", False)]
        if hasattr(Model, "active"):
            domain.extend(["|", ("active", "=", True), ("active", "=", False)])
        records = Model.search(domain).with_context(prefetch_fields=False)
        records_dic = {c[odoo_key]: c.id for c in records if c[odoo_key]}
        return fds_records, records, records_dic

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
        fields_to_update = self.dbsource.fields_to_update_ids.filtered(
            lambda x: x.model_id.model == model_name
        ).mapped("field_ids.name")
        record = specific_record or records.browse(records_dic.get(fds_key, False))
        if record:
            if not update_method:
                return record
            # Performance issue
            # record = records.filtered(lambda x: x.id == record_id)
            values = (update_vals or vals).copy()
            if not force_update:
                for k, v in values.copy().items():
                    if k not in fields_to_update or (
                        record._fields[k].convert_to_write(record[k], record) == v
                    ):
                        values.pop(k)
            if values:
                record.with_context(tracking_disable=True).write(values)
        else:
            Model = self.env[records._name]
            if only_update:
                return Model.browse()
            record = Model.with_context(tracking_disable=True).create(vals)
            records_dic[fds_key] = record.id
        return record

    def get_m2_odoo_id(self, model_name, key_value, field_key=False, return_field="id"):
        return self.dbsource.get_m2_odoo_id(
            model_name, key_value, field_key or self._external_key, return_field
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

    @api.model
    @ormcache("model_name", "key_value", "field_key", "return_field")
    def get_m2_odoo_id(
        self, model_name, key_value, field_key="fds_key", return_field="id"
    ):
        if not key_value:
            return False
        record = self.env[model_name].search_external(key_value, field_key)
        return record.id if return_field == "id" else record[return_field].id

    def _number_iban(self, iban):
        return (iban[4:] + iban[:4]).translate(LETTERS)

    def generate_iban_check_digits(self, iban):
        number_iban = self._number_iban(iban[:2] + "00" + iban[4:])
        return f"{98 - (int(number_iban) % 97):0>2}"

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
        original_vat = vals.pop("vat", False)
        vat = original_vat
        if not vat:
            return vals
        # Clean vat
        vat = (
            vat.replace("-", "")
            .replace(".", "")
            .replace(" ", "")
            .replace("*", "")
            .upper()
        )
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
            raise UserError(_("Debe seleccionar un archivo para importar"))
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
