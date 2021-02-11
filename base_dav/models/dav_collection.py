# Copyright 2019 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
import time
from operator import itemgetter
from urllib.parse import quote_plus

from odoo import api, fields, models, tools

import vobject

# pylint: disable=missing-import-error
from ..controllers.main import PREFIX
from ..radicale.collection import Collection, FileItem, Item


class DavCollection(models.Model):
    _name = 'dav.collection'
    _description = 'A collection accessible via WebDAV'

    name = fields.Char(required=True)
    rights = fields.Selection(
        [
            ("owner_only", "Owner Only"),
            ("owner_write_only", "Owner Write Only"),
            ("authenticated", "Authenticated"),
        ],
        required=True,
        default="owner_only",
    )
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
    domain = fields.Char(
        required=True,
        default='[]',
    )
    field_uuid = fields.Many2one('ir.model.fields')
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
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        for this in self:
            this.url = '%s%s/%s/%s' % (
                base_url,
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
        return list(tools.safe_eval(self.domain, self._eval_context()))

    @api.multi
    def eval(self):
        if not self:
            return self.env['unknown']
        self.ensure_one()
        return self.env[self.model_id.model].search(self._eval_domain())

    @api.multi
    def get_record(self, components):
        self.ensure_one()
        collection_model = self.env[self.model_id.model]

        field_name = self.field_uuid.name or "id"
        domain = [(field_name, '=', components[-1])] + self._eval_domain()
        return collection_model.search(domain, limit=1)

    @api.multi
    def from_vobject(self, item):
        self.ensure_one()

        result = {}
        if self.dav_type == 'calendar':
            if item.name != 'VCALENDAR':
                return None
            if not hasattr(item, 'vevent'):
                return None
            item = item.vevent
        elif self.dav_type == 'addressbook' and item.name != 'VCARD':
            return None

        children = {c.name.lower(): c for c in item.getChildren()}
        for mapping in self.field_mapping_ids:
            name = mapping.name.lower()
            if name not in children:
                continue

            if name in children:
                value = mapping.from_vobject(children[name])
                if value:
                    result[mapping.field_id.name] = value

        return result

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
            value = mapping.to_vobject(record)
            if value:
                vobj.add(mapping.name).value = value

        if 'uid' not in vobj.contents:
            vobj.add('uid').value = '%s,%s' % (record._name, record.id)
        if 'rev' not in vobj.contents and 'write_date' in record._fields:
            vobj.add('rev').value = record.write_date.\
                replace(':', '').replace(' ', 'T').replace('.', '') + 'Z'
        return result

    @api.model
    def _odoo_to_http_datetime(self, value):
        return time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT',
            time.strptime(value, '%Y-%m-%d %H:%M:%S'),
        )

    @api.model
    def _split_path(self, path):
        return list(filter(
            None, os.path.normpath(path or '').strip('/').split('/')
        ))

    @api.multi
    def dav_list(self, collection, path_components):
        self.ensure_one()

        if self.dav_type == 'files':
            if len(path_components) == 3:
                collection_model = self.env[self.model_id.model]
                record = collection_model.browse(map(
                    itemgetter(0),
                    collection_model.name_search(
                        path_components[2], operator='=', limit=1,
                    )
                ))
                return [
                    '/' + '/'.join(
                        path_components + [quote_plus(attachment.name)]
                    )
                    for attachment in self.env['ir.attachment'].search([
                        ('type', '=', 'binary'),
                        ('res_model', '=', record._name),
                        ('res_id', '=', record.id),
                    ])
                ]
            elif len(path_components) == 2:
                return [
                    '/' + '/'.join(
                        path_components + [quote_plus(record.display_name)]
                    )
                    for record in self.eval()
                ]

        if len(path_components) > 2:
            return []

        result = []
        for record in self.eval():
            if self.field_uuid:
                uuid = record[self.field_uuid.name]
            else:
                uuid = str(record.id)
            result.append('/' + '/'.join(path_components + [uuid]))
        return result

    @api.multi
    def dav_delete(self, collection, components):
        self.ensure_one()

        if self.dav_type == "files":
            # TODO: Handle deletion of attachments
            pass
        else:
            self.get_record(components).unlink()

    @api.multi
    def dav_upload(self, collection, href, item):
        self.ensure_one()

        components = self._split_path(href)
        collection_model = self.env[self.model_id.model]
        if self.dav_type == 'files':
            # TODO: Handle upload of attachments
            return None

        data = self.from_vobject(item)
        record = self.get_record(components)

        if not record:
            if self.field_uuid:
                data[self.field_uuid.name] = components[-1]

            record = collection_model.create(data)
            uuid = components[-1] if self.field_uuid else record.id
            href = "%s/%s" % (href, uuid)
        else:
            record.write(data)

        return Item(
            collection,
            item=self.to_vobject(record),
            href=href,
            last_modified=self._odoo_to_http_datetime(record.write_date),
        )

    @api.multi
    def dav_get(self, collection, href):
        self.ensure_one()

        components = self._split_path(href)
        collection_model = self.env[self.model_id.model]
        if self.dav_type == 'files':
            if len(components) == 3:
                result = Collection(href)
                result.logger = self.logger
                return result
            if len(components) == 4:
                record = collection_model.browse(map(
                    itemgetter(0),
                    collection_model.name_search(
                        components[2], operator='=', limit=1,
                    )
                ))
                attachment = self.env['ir.attachment'].search([
                    ('type', '=', 'binary'),
                    ('res_model', '=', record._name),
                    ('res_id', '=', record.id),
                    ('name', '=', components[3]),
                ], limit=1)
                return FileItem(
                    collection,
                    item=attachment,
                    href=href,
                    last_modified=self._odoo_to_http_datetime(
                        record.write_date
                    ),
                )

        record = self.get_record(components)

        if not record:
            return None

        return Item(
            collection,
            item=self.to_vobject(record),
            href=href,
            last_modified=self._odoo_to_http_datetime(record.write_date),
        )
