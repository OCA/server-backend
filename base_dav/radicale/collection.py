# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import os
import operator
import time
from odoo.http import request
from contextlib import contextmanager
try:
    from radicale.storage import BaseCollection, Item, get_etag
except ImportError:
    BaseCollection = None
    Item = None
    get_etag = None


class BytesPretendingToBeString(bytes):
    # radicale expects a string as file content, so we provide the str
    # functions needed
    def encode(self, encoding):
        return self


class FileItem(Item):
    """this item tricks radicalev into serving a plain file"""
    @property
    def name(self):
        return 'VCARD'

    def serialize(self):
        return BytesPretendingToBeString(base64.b64decode(self.item.datas))

    @property
    def etag(self):
        return get_etag(self.item.datas.decode('ascii'))


class Collection(BaseCollection):
    @classmethod
    def static_init(cls):
        pass

    @classmethod
    def _split_path(cls, path):
        return list(filter(
            None, os.path.normpath(path or '').strip('/').split('/')
        ))

    @classmethod
    def discover(cls, path, depth=None):
        depth = int(depth or "0")
        components = cls._split_path(path)
        collection = cls(path)
        if len(components) > 2:
            # TODO: this probably better should happen in some dav.collection
            # function
            if collection.collection.dav_type == 'files' and depth:
                for href in collection.list():
                    yield collection.get(href)
                    return
            yield collection.get(path)
            return
        yield collection
        if depth and len(components) == 1:
            for collection in request.env['dav.collection'].search([]):
                yield cls('/'.join(components + ['/%d' % collection.id]))
        if depth and len(components) == 2:
            for href in collection.list():
                yield collection.get(href)

    @classmethod
    @contextmanager
    def acquire_lock(cls, mode, user=None):
        """We have a database for that"""
        yield

    @property
    def env(self):
        return request.env

    def __init__(self, path):
        self.path_components = self._split_path(path)
        self.path = '/'.join(self.path_components) or '/'
        self.collection = self.env['dav.collection']
        if len(self.path_components) >= 2 and str(
                self.path_components[1]
        ).isdigit():
            self.collection = self.env['dav.collection'].browse(int(
                self.path_components[1]
            ))

    def get(self, href):
        components = self._split_path(href)
        # TODO: this probably better should happen in some dav.collection
        # function
        collection_model = self.env[self.collection.model_id.model]
        if self.collection.dav_type == 'files':
            if len(components) == 3:
                result = Collection(href)
                result.logger = self.logger
                return result
            if len(components) == 4:
                record = collection_model.browse(map(
                    operator.itemgetter(0),
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
                    self,
                    item=attachment,
                    href=href,
                    last_modified=self._odoo_to_http_datetime(
                        record.write_date
                    ),
                )
        record = collection_model.browse(int(components[-1]))
        return Item(
            self,
            item=self.collection.to_vobject(record),
            href=href,
            last_modified=self._odoo_to_http_datetime(record.write_date),
        )

    def _odoo_to_http_datetime(self, value):
        return time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT',
            time.strptime(value, '%Y-%m-%d %H:%M:%S'),
        )

    def get_meta(self, key=None):
        if key is None:
            return {}
        elif key == 'tag':
            return self.collection.tag
        elif key == 'D:displayname':
            return self.collection.display_name
        elif key == 'C:supported-calendar-component-set':
            return 'VTODO,VEVENT,VJOURNAL'
        elif key == 'C:calendar-home-set':
            return None
        elif key == 'D:principal-URL':
            return None
        elif key == 'ICAL:calendar-color':
            # TODO: set in dav.collection
            return '#48c9f4'
        self.logger.warning('unsupported metadata %s', key)

    @property
    def last_modified(self):
        return self._odoo_to_http_datetime(self.collection.create_date)

    def list(self):
        # TODO: this probably better should happen in some dav.collection
        # function
        if self.collection.dav_type == 'files':
            if len(self.path_components) == 3:
                collection_model = self.env[self.collection.model_id.model]
                record = collection_model.browse(map(
                    operator.itemgetter(0),
                    collection_model.name_search(
                        self.path_components[2], operator='=', limit=1,
                    )
                ))
                return [
                    '/' + '/'.join(
                        # TODO: take care somewhere that we have no invalid
                        # characters here
                        self.path_components + [attachment.name]
                    )
                    for attachment in self.env['ir.attachment'].search([
                        ('type', '=', 'binary'),
                        ('res_model', '=', record._name),
                        ('res_id', '=', record.id),
                    ])
                ]
            elif len(self.path_components) == 2:
                return [
                    '/' + '/'.join(
                        # TODO: take care somewhere that we have no invalid
                        # characters here
                        self.path_components + [record.display_name]
                    )
                    for record in self.collection.eval()
                ]
        if len(self.path_components) > 2:
            return []
        return [
            '/' + '/'.join(self.path_components + [str(record.id)])
            for record in self.collection.eval()
        ]
