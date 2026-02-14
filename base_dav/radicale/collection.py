# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import contextlib
import logging
from collections.abc import Callable
from contextlib import AbstractContextManager

from radicale import pathutils
from radicale.item import Item as RadicaleItem
from radicale.storage import BaseCollection, BaseStorage

from odoo.http import request

_logger = logging.getLogger("radicale")


def _norm_path(path):
    """Return sanitized Radicale path without leading slash.

    Applies Radicale path sanitization and removes leading slash.

    :param path: Raw path string
    :type path: str

    :return: Normalized path without leading slash
    :rtype: str
    """
    return pathutils.strip_path(pathutils.sanitize_path(path or ""))


def _abs_href(collection_path, href):
    """Build absolute href for Radicale item.

    Ensures href is prefixed with collection path and leading slash.

    :param collection_path: Collection base path
    :type collection_path: str
    :param href: Relative or raw href
    :type href: str

    :return: Absolute href
    :rtype: str
    """
    h = pathutils.strip_path(pathutils.sanitize_path(href or ""))
    prefix = _norm_path(collection_path)
    if prefix:
        pref = f"{prefix}/"
        if h.startswith(pref):
            return f"/{h}"
        return f"/{pref}{h}"
    return f"/{h}"


def _rel_href(collection_path, href):
    """Convert absolute href to relative href.

    Removes collection prefix if present.

    :param collection_path: Collection base path
    :type collection_path: str
    :param href: Absolute href
    :type href: str

    :return: Relative href
    :rtype: str
    """
    if not href:
        return href
    h = pathutils.strip_path(pathutils.sanitize_path(href))
    prefix = _norm_path(collection_path)
    if prefix:
        pref = f"{prefix}/"
        if h.startswith(pref):
            return h[len(pref) :]
    return h


class Item(RadicaleItem):
    def __init__(self, collection, item, href, last_modified):
        """Initialize Radicale item wrapper for Odoo DAV.

        :param collection: DAV collection instance
        :type collection: Collection
        :param item: vobject instance
        :type item: Any
        :param href: Item href
        :type href: str
        :param last_modified: HTTP formatted datetime string
        :type last_modified: str
        """
        super().__init__(
            collection=collection,
            vobject_item=item,
            href=_rel_href(collection.path, href),
            last_modified=last_modified or "",
        )


class FileItem(RadicaleItem):
    def __init__(self, collection, href, attachment, last_modified):
        """Initialize Radicale file item from Odoo attachment.

        Decodes binary attachment data into UTF-8 text.

        :param collection: DAV collection instance
        :type collection: Collection
        :param href: File href
        :type href: str
        :param attachment: ir.attachment record
        :type attachment: Any
        :param last_modified: HTTP formatted datetime, defaults to ""
        :type last_modified: str, optional
        """
        raw = b""
        datas = getattr(attachment, "datas", None)
        if datas:
            try:
                raw = base64.b64decode(datas)
            except Exception:
                raw = b""
        text = raw.decode("utf-8", errors="ignore")

        super().__init__(
            collection=collection,
            text=text,
            href=_rel_href(collection.path, href),
            last_modified=last_modified or "",
        )


class Collection(BaseCollection):
    """
    Path forms:
      - root: "" or "/"
      - principal: "admin"
      - odoo collection: "admin/<collection_id>"
      - item: "admin/<collection_id>/<href>"
    """

    def __init__(self, path):
        """Initialize DAV collection from Radicale path.

        Supports:
          - root
          - principal
          - Odoo collection
          - collection item

        :param path: Radicale collection path
        :type path: str
        """
        self.logger = _logger
        self._path = _norm_path(path)
        self.path_components = self._path.split("/", 2) if self._path else [""]

        env = request.env
        self._record = None
        if len(self.path_components) > 1 and (self.path_components[1] or "").isdigit():
            rec = env["dav.collection"].browse(int(self.path_components[1])).exists()
            self._record = rec or None

    @property
    def path(self):
        """Return normalized collection path.

        :return: Collection path
        :rtype: str
        """
        return self._path

    def get_multi(self, hrefs):
        """Retrieve multiple items by href.

        Skips duplicate hrefs.

        :param hrefs: Iterable of href strings
        :type hrefs: Iterable[str]

        :return: Iterator of (href, item)
        :rtype: Iterator[Tuple[str, Optional[Any]]]
        """
        seen: set[str] = set()
        for href in hrefs:
            if href in seen:
                continue
            seen.add(href)
            yield href, self.get(href)

    def get_all(self):
        """Yield all items in collection.

        :return: Iterator of Radicale items
        :rtype: Iterator[Any]
        """
        for href in self.list():
            item = self.get(href)
            if item is not None:
                yield item

    def list(self):
        """Return relative hrefs for items or child collections.

        Behavior depends on path type:
          - collection
          - principal
          - root

        :return: Iterable of relative hrefs
        :rtype: Iterable[str]
        """
        env = request.env

        # real DAV collection -> list items
        if self._record:
            hrefs = self._record.dav_list(self, self.path_components)
            for h in hrefs:
                yield _rel_href(self.path, h)
            return

        # principal -> list collections
        if self.is_principal:
            login = self.path_components[0]
            for rec in env["dav.collection"].search([]):
                yield f"{login}/{rec.id}"
            return

        # root -> expose only current user principal
        current = env.user.login
        if current:
            yield current

    def get(self, href):
        """Retrieve single DAV item by href.

        :param href: Relative href
        :type href: str

        :return: Radicale item or None
        :rtype: Optional[Any]
        """
        if not self._record:
            return None
        abs_href = _abs_href(self.path, href)
        return self._record.dav_get(self, abs_href)

    def upload(self, href, item, **kwargs):
        """Upload or update DAV item.

        :param href: Relative href
        :type href: str
        :param item: RadicaleItem or vobject
        :type item: Any
        :param kwargs: Additional Radicale parameters
        :type kwargs: Any

        :return: Tuple of (uploaded_item, previous_item)
        :rtype: Tuple[Optional[Any], Optional[Any]]
        """
        if not self._record:
            raise ValueError(f"Not a DAV collection: {self.path!r}")

        old_item = self.get(href)

        # tests may pass vobject directly;
        # Radicale passes RadicaleItem with .vobject_item
        vobj = getattr(item, "vobject_item", None) or item
        abs_href = _abs_href(self.path, href)

        uploaded = self._record.dav_upload(self, abs_href, vobj)
        return uploaded, old_item

    def delete(self, href: str | None = None):
        """Delete DAV item.

        :param href: Relative href, defaults to None
        :type href: Optional[str], optional

        :raises ValueError: If not a DAV collection
        :raises NotImplementedError: If deleting collection root
        """
        if not self._record:
            raise ValueError(f"Not a DAV collection: {self.path!r}")
        if not href:
            raise NotImplementedError("Deleting collections is not supported")
        abs_href = _abs_href(self.path, href)
        self._record.dav_delete(self, abs_href)

    def get_meta(self, key: str | None = None):
        """Return collection metadata value.

        :param key: Metadata key, defaults to None
        :type key: Optional[str], optional

        :return: Metadata value or mapping
        :rtype: Mapping[str, str] | str | None
        """
        if key is None:
            return {}

        if not self._record:
            return None

        if key == "tag":
            return self._record.tag
        if key == "D:displayname":
            return self._record.display_name or self._record.name
        if key == "C:supported-calendar-component-set":
            return "VTODO,VEVENT,VJOURNAL"
        if key == "ICAL:calendar-color":
            return "#48c9f4"
        self.logger.warning("unsupported metadata %s", key)
        return None

    @property
    def last_modified(self):
        """Return HTTP last modified timestamp for collection.

        :return: HTTP datetime string
        :rtype: str
        """
        if not self._record:
            return ""
        # reuse helper from dav.collection
        return self._record._odoo_to_http_datetime(self._record.create_date) or ""


class Storage(BaseStorage):
    def discover(
        self,
        path,
        depth="0",
        child_context_manager: Callable[[str, str | None], AbstractContextManager[None]]
        | None = None,
        user_groups: set[str] | None = None,
    ):
        """Discover collections or items for given path.

        Supports depth 0 and depth > 0 discovery.

        :param path: Radicale path
        :type path: str
        :param depth: Discovery depth, defaults to "0"
        :type depth: str, optional
        :param child_context_manager: Optional Radicale context manager
        :type child_context_manager: Optional[Callable]
        :param user_groups: Optional set of user groups
        :type user_groups: Optional[set[str]]

        :return: Iterator of collections or items
        :rtype: Iterator[Any]
        """
        path = _norm_path(path)
        parts = path.split("/", 2) if path else [""]

        # item path: "admin/2/2"
        if len(parts) == 3 and (parts[1] or "").isdigit():
            coll = Collection("/".join(parts[:2]))
            if not getattr(coll, "_record", None):
                return iter(())
            item = coll.get(parts[2])
            return iter([item]) if item else iter(())

        coll = Collection(path)

        if depth == "0":
            return iter([coll])

        # depth != 0 -> include direct children
        children = [coll]
        if getattr(coll, "_record", None):
            children.extend(list(coll.get_all()))
        else:
            for child_path in coll.list():
                children.append(Collection(child_path))

        return iter(children)

    def move(self, item: RadicaleItem, to_collection: BaseCollection, to_href):
        """Move DAV item between collections.

        :raises NotImplementedError: MOVE is not supported

        :param item: Radicale item
        :type item: RadicaleItem
        :param to_collection: Target collection
        :type to_collection: BaseCollection
        :param to_href: Target href
        :type to_href: str
        """
        raise NotImplementedError("MOVE is not supported by Odoo DAV backend")

    def create_collection(self, href, items=None, props=None):
        """Create DAV collection.

        :raises NotImplementedError: MKCOL not supported

        :param href: Collection href
        :type href: str
        :param items: Optional initial items
        :type items: Optional[Iterable[Any]]
        :param props: Optional collection properties
        :type props: Optional[Mapping[str, Any]]

        :return: Collection instance
        :rtype: BaseCollection
        """
        raise NotImplementedError("MKCOL is not supported by Odoo DAV backend")

    @contextlib.contextmanager
    def acquire_lock(self, mode, user=None, **kwargs):
        """Acquire storage lock.

        Locking is delegated to database transactions.

        :param mode: Lock mode
        :type mode: str
        :param user: Optional user identifier
        :type user: Optional[str]
        :param kwargs: Additional parameters
        :type kwargs: Any

        :yield: None
        """
        # DB is the lock
        yield

    def verify(self):
        """Verify storage backend integrity.

        Always returns True for Odoo backend.

        :return: Verification status
        :rtype: bool
        """
        return True
