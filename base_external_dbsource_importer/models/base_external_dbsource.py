# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import string

from odoo import api, fields, models
from odoo.tools import ormcache

_logger = logging.getLogger(__name__)

LETTERS = {ord(d): str(i) for i, d in enumerate(string.digits + string.ascii_uppercase)}


class BaseExternalModel:
    _name = "base.external.model"

    def __init__(self, cr, rows, cols):
        self._cr = cr
        self.rows = rows
        self.cols = cols
        self.index = 0

    def __getattr__(self, attrib):
        return self[self.cols[attrib]]

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.rows):
            raise StopIteration("There is no elements")
        row = self.rows[self.index]
        self.index += 1
        return row

    def __len__(self):
        return len(self.rows)


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
        sql = "SELECT {} FROM {} {};".format(fields, table_name, where)
        rows, cols = self.execute_query(sql, [], metadata=True)
        fds_records = BaseExternalModel(self.env.cr, rows, cols)
        return fds_records

    def load_data(
        self,
        model_name,
        table_name,
        fields="*",
        where="",
        odoo_key="",
        load_all_odoo_records=False,
    ):
        odoo_key = odoo_key or self._external_key
        Model = self.env[model_name]
        fds_records = self._get_external_records(table_name, fields=fields, where=where)
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


class BaseExternalDbsource(models.Model):
    """It provides logic for connection to a MySQL data source."""

    _inherit = "base.external.dbsource"

    fields_to_update_ids = fields.One2many(
        comodel_name="base.external.dbsource.fields.update",
        inverse_name="db_source_id",
        string="Fields To Update",
    )
    only_update = fields.Boolean(string="Only update values", default=True)

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
        return "{:0>2}".format(98 - (int(number_iban) % 97))

    @api.model
    @ormcache("code")
    def _state_country_from_zip(self, code=None):
        CityZip = city_zip = self.env["res.city.zip"]
        if code:
            city_zip = CityZip.search([("name", "=", code)], limit=1)
        return (
            city_zip.city_id.state_id.id,
            city_zip.city_id.country_id.id,
            city_zip.city_id.country_id.code,
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
        full_vat = "{}{}".format(country_code.upper(), vat)
        if ResPartner.simple_vat_check(country_code.lower(), vat):
            vals["vat"] = full_vat
        else:
            if vals.get("comment", False):
                vals["comment"] += "\nVAT: {}".format(original_vat)
            else:
                vals["comment"] = "VAT: {}".format(original_vat)
        return vals


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
