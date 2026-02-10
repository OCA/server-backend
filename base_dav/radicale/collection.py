# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import logging
import os
from datetime import timezone
from contextlib import contextmanager

from odoo import fields
from odoo.http import request

try:
    from radicale.storage import BaseCollection, Item, get_etag
except ImportError:
    BaseCollection = None
    Item = None
    get_etag = None

_LOGGER = logging.getLogger(__name__)


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

    @property
    def last_modified(self):
        return self._odoo_to_http_datetime(self.collection.create_date)

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

    def get(self, href):
        if hasattr(href, "href"):
            href = href.href
        item = self.collection.dav_get(self, href)
        if not item:
            _LOGGER.info(
                "CardDAV Storage: get miss path=%s href=%s",
                self.path,
                href,
            )
        return item

    def upload(self, href, vobject_item):
        return self.collection.dav_upload(self, href, vobject_item)

    def delete(self, href):
        return self.collection.dav_delete(self, self._split_path(href))

    def list(self):
        hrefs = self.collection.dav_list(self, self.path_components)
        _LOGGER.info(
            "CardDAV Storage: list path=%s count=%s sample=%s",
            self.path,
            len(hrefs),
            hrefs[:3],
        )
        return hrefs

    def _relative_hrefs(self, hrefs):
        rel = []
        for href in hrefs:
            parts = self._split_path(href)
            if not parts:
                continue
            rel.append(parts[-1])
        return rel

    # Radicale v2 uses pre_filtered_list() for REPORT queries.
    # Return hrefs and let Radicale fetch items via get()/get_multi().
    def pre_filtered_list(self, filters):
        hrefs = self._relative_hrefs(self.list())
        _LOGGER.info(
            "CardDAV Storage: pre_filtered_list path=%s filters=%s count=%s",
            self.path,
            bool(filters),
            len(hrefs),
        )
        return hrefs

    def get_multi(self, hrefs):
        items = [item for item in (self.get(href) for href in hrefs) if item]
        _LOGGER.info(
            "CardDAV Storage: get_multi path=%s requested=%s returned=%s",
            self.path,
            len(hrefs),
            len(items),
        )
        return items

    def get_all(self):
        hrefs = self._relative_hrefs(self.list())
        items = [item for item in (self.get(href) for href in hrefs) if item]
        _LOGGER.info(
            "CardDAV Storage: get_all path=%s returned=%s",
            self.path,
            len(items),
        )
        return items

    def get_all_filtered(self, filters):
        items = self.get_all()
        empty_filter = bool(filters) and all(
            len(filter_) == 0 for filter_ in filters
        )
        _LOGGER.info(
            (
                "CardDAV Storage: get_all_filtered path=%s filters=%s "
                "empty_filter=%s returned=%s"
            ),
            self.path,
            len(filters or []),
            empty_filter,
            len(items),
        )
        # Linphone sends <card:filter/> (no children) for addressbook-query.
        # Radicale's generic matcher treats that as no match, so mark filters as
        # already matched in this case to return all addressbook items.
        # Keep this behavior unless client-side filter semantics are revisited.
        return ((item, empty_filter) for item in items)

    def get_filtered(self, filters):
        items = self.get_all()
        _LOGGER.info(
            "CardDAV Storage: get_filtered path=%s filters=%s returned=%s",
            self.path,
            bool(filters),
            len(items),
        )
        for item in items:
            yield item, True
