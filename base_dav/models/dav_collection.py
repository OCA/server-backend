# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import vobject
from odoo import api, fields, models, tools
# pylint: disable=missing-import-error
from ..controllers.main import PREFIX


class DavCollection(models.Model):
    _name = 'dav.collection'
    _description = 'A collection accessible via WebDAV'

    name = fields.Char(required=True)
    dav_type = fields.Selection(
        [
            ('calendar', 'Calendar'),
            ('addressbook', 'Addressbook'),
            ('files', 'Files'),
        ],
        string='Type',
        required=True,
        default='calendar',
    )
    tag = fields.Char(compute='_compute_tag')
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        domain=[('transient', '=', False)],
    )
    domain = fields.Text(
        required=True,
        default='[]',
    )
    field_mapping_ids = fields.One2many(
        'dav.collection.field_mapping',
        'collection_id',
        string='Field mappings',
    )
    url = fields.Char(compute='_compute_url')

    @api.multi
    def _compute_tag(self):
        for this in self:
            if this.dav_type == 'calendar':
                this.tag = 'VCALENDAR'
            elif this.dav_type == 'addressbook':
                this.tag = 'VADDRESSBOOK'

    @api.multi
    def _compute_url(self):
        for this in self:
            this.url = '%s%s/%s/%s' % (
                self.env['ir.config_parameter'].get_param('web.base.url'),
                PREFIX,
                self.env.user.login,
                this.id,
            )

    @api.constrains('domain')
    def _check_domain(self):
        self._eval_domain()

    @api.model
    def _eval_context(self):
        return {
            'user': self.env.user,
        }

    @api.multi
    def _eval_domain(self):
        self.ensure_one()
        return tools.safe_eval(self.domain, self._eval_context())

    @api.multi
    def eval(self):
        if not self:
            return self.env['unknown']
        self.ensure_one()
        return self.env[self.model_id.model].search(
            self._eval_domain()
        )

    @api.multi
    def to_vobject(self, record):
        self.ensure_one()
        result = None
        vobj = None
        if self.dav_type == 'calendar':
            result = vobject.iCalendar()
            vobj = result.add('vevent')
        if self.dav_type == 'addressbook':
            result = vobject.vCard()
            vobj = result
        for mapping in self.field_mapping_ids:
            conversion_funcs = [
                '_to_vobject_%s_%s' % (
                    mapping.field_id.ttype, mapping.name.lower()
                ),
                '_to_vobject_%s' % mapping.field_id.ttype,
            ]
            value = record[mapping.field_id.name]
            for conversion_func in conversion_funcs:
                if hasattr(self, conversion_func):
                    value = getattr(self, conversion_func)(
                        record, mapping.field_id.name
                    )
                    break
            if not value:
                continue
            vobj.add(mapping.name).value = value
        if 'uid' not in vobj.contents:
            vobj.add('uid').value = '%s,%s' % (record._name, record.id)
        if 'rev' not in vobj.contents and 'write_date' in record._fields:
            vobj.add('rev').value = self._to_vobject_datetime_rev(
                record, 'write_date',
            )
        return result

    @api.multi
    def _to_vobject_datetime(self, record, field_name):
        result = fields.Datetime.from_string(record[field_name])
        # TODO: this still generates wrong times
        result.replace(tzinfo=vobject.icalendar.utc)
        return result

    @api.multi
    def _to_vobject_datetime_rev(self, record, field_name):
        return record[field_name] and record[field_name]\
            .replace('-', '').replace(' ', 'T').replace(':', '') + 'Z'

    @api.multi
    def _to_vobject_date(self, record, field_name):
        return fields.Date.from_string(record[field_name])

    @api.multi
    def _to_vobject_binary(self, record, field_name):
        return record[field_name] and record[field_name].decode('ascii')

    @api.multi
    def _to_vobject_char_n(self, record, field_name):
        # TODO: how are we going to handle compound types like this?
        return vobject.vcard.Name(family=record[field_name])
