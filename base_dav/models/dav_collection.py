# Copyright 2019 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import os
from datetime import timezone
from operator import itemgetter
from urllib.parse import quote_plus

from odoo import api, fields, models, tools
from odoo.tools.safe_eval import safe_eval

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
        ondelete='cascade',
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

    @api.model
    def _ensure_default_addressbook(self):
        icp = self.env["ir.config_parameter"].sudo()
        collection_id = icp.get_param("base_dav.default_addressbook_id")
        collection = (
            self.sudo().browse(int(collection_id))
            if collection_id else self.browse()
        )
        if not (collection and collection.exists()):
            collection = self.sudo().search(
                [
                    ("dav_type", "=", "addressbook"),
                    ("model_id.model", "=", "res.partner"),
                ],
                limit=1,
            )
            if not collection:
                partner_model = self.env["ir.model"].sudo().search(
                    [("model", "=", "res.partner")], limit=1
                )
                collection = self.sudo().create(
                    {
                        "name": "Contacts",
                        "dav_type": "addressbook",
                        "model_id": partner_model.id,
                        "domain": "[]",
                    }
                )

        icp.set_param("base_dav.default_addressbook_id", str(collection.id))

        mappings = [
            ("N", "name"),
            ("FN", "display_name"),
            ("EMAIL", "email"),
            ("TEL", "phone"),
            ("TEL", "mobile"),
        ]
        mapping_model = self.env["dav.collection.field_mapping"].sudo()
        fields_model = self.env["ir.model.fields"].sudo()
        for vcard_name, field_name in mappings:
            field_id = fields_model.search(
                [
                    ("model", "=", "res.partner"),
                    ("name", "=", field_name),
                ],
                limit=1,
            )
            if not field_id:
                continue
            exists = mapping_model.search(
                [
                    ("collection_id", "=", collection.id),
                    ("name", "=", vcard_name),
                    ("field_id", "=", field_id.id),
                ],
                limit=1,
            )
            if exists:
                continue
            mapping_model.create(
                {
                    "collection_id": collection.id,
                    "name": vcard_name,
                    "field_id": field_id.id,
                    "mapping_type": "simple",
                }
            )

        return collection

    @api.depends("dav_type")
    def _compute_tag(self):
        for record in self:
            if record.dav_type == "calendar":
                record.tag = "VCALENDAR"
            elif record.dav_type == "addressbook":
                record.tag = "VADDRESSBOOK"
            else:
                record.tag = False

    def _compute_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        for record in self:
            if base_url and record.id:
                record.url = "%s%s/%s/%s" % (
                    base_url,
                    PREFIX,
                    self.env.user.login,
                    record.id,
                )
            else:
                record.url = False

    @api.constrains('domain')
    def _check_domain(self):
        self._eval_domain()

    @api.model
    def _eval_context(self):
        return {
            'user': self.env.user,
        }

    def _eval_domain(self):
        self.ensure_one()
        return list(safe_eval(self.domain, self._eval_context()))

    def eval(self):
        if not self:
            return self.env['unknown']
        self.ensure_one()
        return self.env[self.model_id.model].search(self._eval_domain())

    def get_record(self, components):
        self.ensure_one()
        collection_model = self.env[self.model_id.model]

        field_name = self.field_uuid.name or "id"
        domain = [(field_name, '=', components[-1])] + self._eval_domain()
        return collection_model.search(domain, limit=1)

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
            if self.dav_type == "addressbook" and name == "photo":
                continue
            if name not in children:
                continue

            if name in children:
                value = mapping.from_vobject(children[name])
                if value:
                    result[mapping.field_id.name] = value

        return result

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
            if 'version' in vobj.contents:
                vobj.contents['version'][0].value = '4.0'
            else:
                vobj.add('version').value = '4.0'
            if 'kind' not in vobj.contents:
                vobj.add('kind').value = 'individual'
        for mapping in self.field_mapping_ids:
            if self.dav_type == "addressbook" and mapping.name.lower() == "photo":
                continue
            value = mapping.to_vobject(record)
            if value:
                vobj.add(mapping.name).value = value

        if self.dav_type == 'addressbook' and 'fn' not in vobj.contents:
            display_name = record.display_name or record.name or ''
            if display_name:
                vobj.add('fn').value = display_name
        if 'uid' not in vobj.contents:
            vobj.add('uid').value = '%s,%s' % (record._name, record.id)
        if 'rev' not in vobj.contents and 'write_date' in record._fields:
            write_date = fields.Datetime.to_datetime(record.write_date)
            if write_date:
                if write_date.tzinfo:
                    write_date = write_date.astimezone(timezone.utc)
                else:
                    write_date = write_date.replace(tzinfo=timezone.utc)
                vobj.add('rev').value = write_date.strftime(
                    '%Y%m%dT%H%M%SZ'
                )
        return result

    @api.model
    def _odoo_to_http_datetime(self, value):
        if not value:
            return None
        date_value = fields.Datetime.to_datetime(value)
        if not date_value:
            return None
        if date_value.tzinfo:
            date_value = date_value.astimezone(timezone.utc)
        else:
            date_value = date_value.replace(tzinfo=timezone.utc)
        return date_value.strftime('%a, %d %b %Y %H:%M:%S GMT')

    @api.model
    def _split_path(self, path):
        return list(filter(
            None, os.path.normpath(path or '').strip('/').split('/')
        ))

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
            # Use absolute item hrefs so rights checks receive the full DAV path.
            result.append('/' + '/'.join(path_components + [str(uuid)]))
        return result

    def dav_delete(self, collection, components):
        self.ensure_one()

        if self.dav_type == "files":
            # TODO: Handle deletion of attachments
            pass
        else:
            self.get_record(components).unlink()

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
