# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import base64
import logging
import os
import time
from contextlib import contextmanager

from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    from radicale import item as radicale_item
    from radicale.storage import BaseCollection as RadicaleBaseCollection
    from radicale.storage import BaseStorage as RadicaleBaseStorage
except ImportError:
    RadicaleBaseCollection = object
    RadicaleBaseStorage = object
    radicale_item = None


class BytesPretendingToBeString(bytes):
    def encode(self, encoding):
        return self


class FileItem:
    def __init__(self, collection, item, href, last_modified):
        self.collection = collection
        self._item = item
        self.href = href
        self.last_modified = last_modified

    @property
    def name(self):
        return "VCARD"

    def serialize(self):
        return BytesPretendingToBeString(base64.b64decode(self._item.datas))

    @property
    def etag(self):
        return self._item.datas.decode("ascii")


class Item:
    def __init__(self, collection, item, href, last_modified):
        self.collection = collection
        self._item = item
        self.href = href
        self.last_modified = last_modified

    @property
    def component_name(self):
        if hasattr(self._item, "name"):
            return self._item.name
        return None

    @property
    def uid(self):
        if hasattr(self._item, "uid") and self._item.uid:
            return self._item.uid.value
        return self.href

    @property
    def etag(self):
        if hasattr(self._item, "etag"):
            return self._item.etag
        return '""'

    def serialize(self):
        return self._item.serialize()

    def time_range(self):
        return (None, None)


class Collection(RadicaleBaseCollection):
    @classmethod
    def _split_path(cls, path):
        return list(filter(None, os.path.normpath(path or "").strip("/").split("/")))

    @classmethod
    def _decode_path(cls, path):
        from urllib.parse import unquote

        return unquote(path)

    def __init__(self, path, parent=None, principal=None, folder=None):
        self.path_components = self._split_path(path)
        self._collection = None
        if len(self.path_components) >= 2 and str(self.path_components[1]).isdigit():
            try:
                self._collection = request.env["dav.collection"].browse(
                    int(self.path_components[1])
                )
            except Exception:
                _logger.debug("Could not resolve dav.collection", exc_info=True)

    @property
    def path(self):
        return "/".join(self.path_components) or "/"

    @property
    def collection(self):
        if self._collection:
            try:
                return self._collection.exists()
            except Exception:
                _logger.debug("dav.collection no longer exists", exc_info=True)
        return self._collection

    @property
    def owner(self):
        if len(self.path_components) >= 1:
            return self.path_components[0]
        return ""

    @property
    def is_principal(self):
        return bool(self.path) and "/" not in self.path and self.path != ""

    def get_multi(self, hrefs):
        for href in hrefs:
            item = self.get(href)
            if item:
                yield href, item
            else:
                yield href, None

    def get_all(self):
        if not self.collection:
            return
        path_components = self.path_components
        if len(path_components) == 2:
            try:
                for href in self.collection.dav_list(self, path_components):
                    item = self.get(href)
                    if item:
                        yield item
            except Exception:
                _logger.debug("Could not list dav.collection items", exc_info=True)

    def upload(self, href, item):
        if not self.collection:
            raise Exception("Collection not found")
        return self.collection.dav_upload(self, href, item)

    def delete(self, href=None):
        if not self.collection:
            raise Exception("Collection not found")
        components = self._split_path(href)
        self.collection.dav_delete(self, components)

    def get_meta(self, key=None):
        if not self.collection:
            return {} if key is None else None
        if key is None:
            return {}
        elif key == "tag":
            return self.collection.tag
        elif key == "D:displayname":
            has_display_name = hasattr(self.collection, "display_name")
            return self.collection.display_name if has_display_name else None
        elif key == "C:supported-calendar-component-set":
            return "VTODO,VEVENT,VJOURNAL"
        elif key == "C:calendar-home-set":
            return None
        elif key == "D:principal-URL":
            return None
        elif key == "ICAL:calendar-color":
            return "#48c9f4"
        return None

    def set_meta(self, props):
        pass

    @property
    def last_modified(self):
        if self.collection and hasattr(self.collection, "create_date"):
            return self._odoo_to_http_datetime(self.collection.create_date)
        return self._odoo_to_http_datetime("2024-01-01 00:00:00")

    def _odoo_to_http_datetime(self, value):
        return time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT",
            time.strptime(value, "%Y-%m-%d %H:%M:%S"),
        )

    def get(self, href):
        if not self.collection:
            return None
        try:
            return self.collection.dav_get(self, href)
        except Exception:
            return None

    def sync(self, old_token=""):
        def hrefs_iter():
            for item in self.get_all():
                if item.href:
                    yield item.href

        token = "http://radicale.org/ns/sync/%s" % self.etag.strip('"')
        if old_token:
            raise ValueError("Sync tokens are not supported")
        return token, hrefs_iter()

    def has_uid(self, uid):
        for item in self.get_all():
            if item.uid == uid:
                return True
        return False


class Storage(RadicaleBaseStorage):
    def __init__(self, configuration):
        self.configuration = configuration

    def discover(self, path, depth="0", child_context_manager=None, user_groups=None):
        if user_groups is None:
            user_groups = set()
        path = self._decode_path(path)
        components = Collection._split_path(path)
        collection = Collection(path)

        if len(components) > 2:
            if (
                collection.collection
                and collection.collection.dav_type == "files"
                and depth
            ):
                for href in collection.list():
                    yield collection.get(href)
                    return
            col = collection.get(path)
            if col:
                yield col
            return
        yield collection
        if depth and len(components) == 1:
            try:
                for coll in request.env["dav.collection"].search([]):
                    yield Collection("/".join(components + ["/%d" % coll.id]))
            except Exception:
                _logger.debug("Could not list dav.collection records", exc_info=True)
        if depth and len(components) == 2:
            try:
                for href in collection.dav_list(collection, components):
                    item = collection.get(href)
                    if item:
                        yield item
            except Exception:
                _logger.debug("Could not list dav.collection items", exc_info=True)

    def list(self):
        try:
            for coll in request.env["dav.collection"].search([]):
                yield "/%d" % coll.id
        except Exception:
            _logger.debug("Could not list dav.collection records", exc_info=True)

    @contextmanager
    def acquire_lock(self, mode, user="", *args, **kwargs):
        yield

    def create_collection(self, href, items=None, props=None):
        pass

    def move(self, item, to_collection, to_href):
        pass

    def verify(self):
        return True

    @classmethod
    def _decode_path(cls, path):
        from urllib.parse import unquote

        return unquote(path)
