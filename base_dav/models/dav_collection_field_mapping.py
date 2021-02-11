# Copyright 2019 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import api, fields, models, tools

import dateutil
import vobject
from dateutil import tz


class DavCollectionFieldMapping(models.Model):
    _name = 'dav.collection.field_mapping'
    _description = 'A field mapping for a WebDAV collection'

    collection_id = fields.Many2one(
        'dav.collection', required=True, ondelete='cascade',
    )
    name = fields.Char(
        required=True,
        help="Attribute name in the vobject",
    )
    mapping_type = fields.Selection(
        [
            ('simple', 'Simple'),
            ('code', 'Code'),
        ],
        default='simple',
        required=True,
    )
    field_id = fields.Many2one(
        'ir.model.fields',
        required=True,
        help="Field of the model the values are mapped to",
    )
    model_id = fields.Many2one(
        'ir.model',
        related='collection_id.model_id',
    )
    import_code = fields.Text(
        help="Code to import the value from a vobject. Use the variable "
             "result for the output of the value and item as input"
    )
    export_code = fields.Text(
        help="Code to export the value to a vobject. Use the variable "
             "result for the output of the value and record as input"
    )

    @api.multi
    def from_vobject(self, child):
        self.ensure_one()
        if self.mapping_type == 'code':
            return self._from_vobject_code(child)
        return self._from_vobject_simple(child)

    @api.multi
    def _from_vobject_code(self, child):
        self.ensure_one()
        context = {
            'datetime': datetime,
            'dateutil': dateutil,
            'item': child,
            'result': None,
            'tools': tools,
            'tz': tz,
            'vobject': vobject,
        }
        tools.safe_eval(self.import_code, context, mode="exec", nocopy=True)
        return context.get('result', {})

    @api.multi
    def _from_vobject_simple(self, child):
        self.ensure_one()
        name = self.name.lower()
        conversion_funcs = [
            '_from_vobject_%s_%s' % (self.field_id.ttype, name),
            '_from_vobject_%s' % self.field_id.ttype,
        ]

        for conversion_func in conversion_funcs:
            if hasattr(self, conversion_func):
                value = getattr(self, conversion_func)(child)
                if value:
                    return value

        return child.value

    @api.model
    def _from_vobject_datetime(self, item):
        if isinstance(item.value, datetime.datetime):
            value = item.value.astimezone(dateutil.tz.UTC)
            return value.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        elif isinstance(item.value, datetime.date):
            return item.value.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        return None

    @api.model
    def _from_vobject_date(self, item):
        if isinstance(item.value, datetime.datetime):
            value = item.value.astimezone(dateutil.tz.UTC)
            return value.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        elif isinstance(item.value, datetime.date):
            return item.value.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        return None

    @api.model
    def _from_vobject_binary(self, item):
        return item.value.encode('ascii')

    @api.model
    def _from_vobject_char_n(self, item):
        return item.family

    @api.multi
    def to_vobject(self, record):
        self.ensure_one()
        if self.mapping_type == 'code':
            result = self._to_vobject_code(record)
        else:
            result = self._to_vobject_simple(record)

        if isinstance(result, datetime.datetime) and not result.tzinfo:
            return result.replace(tzinfo=tz.UTC)
        return result

    @api.multi
    def _to_vobject_code(self, record):
        self.ensure_one()
        context = {
            'datetime': datetime,
            'dateutil': dateutil,
            'record': record,
            'result': None,
            'tools': tools,
            'tz': tz,
            'vobject': vobject,
        }
        tools.safe_eval(self.export_code, context, mode="exec", nocopy=True)
        return context.get('result', None)

    @api.multi
    def _to_vobject_simple(self, record):
        self.ensure_one()
        conversion_funcs = [
            '_to_vobject_%s_%s' % (
                self.field_id.ttype, self.name.lower()
            ),
            '_to_vobject_%s' % self.field_id.ttype,
        ]
        value = record[self.field_id.name]
        for conversion_func in conversion_funcs:
            if hasattr(self, conversion_func):
                return getattr(self, conversion_func)(value)
        return value

    @api.model
    def _to_vobject_datetime(self, value):
        result = fields.Datetime.from_string(value)
        return result.replace(tzinfo=tz.UTC)

    @api.model
    def _to_vobject_datetime_rev(self, value):
        return value and value\
            .replace('-', '').replace(' ', 'T').replace(':', '') + 'Z'

    @api.model
    def _to_vobject_date(self, value):
        return fields.Date.from_string(value)

    @api.model
    def _to_vobject_binary(self, value):
        return value and value.decode('ascii')

    @api.model
    def _to_vobject_char_n(self, value):
        # TODO: how are we going to handle compound types like this?
        return vobject.vcard.Name(family=value)
