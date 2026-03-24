# Copyright 2019 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import posixpath
import time
from operator import itemgetter
from urllib.parse import quote_plus, unquote_plus

import vobject

from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

from ..controllers.main import PREFIX

_DAV_ITEM_EXTENSIONS = (".vcf", ".ics")


def _dav_strip_item_extension(name: str) -> str:
    """Return DAV item identifier without common extensions (.vcf/.ics)."""
    name = (name or "").strip()
    lower = name.lower()
    for ext in _DAV_ITEM_EXTENSIONS:
        if lower.endswith(ext):
            return name[: -len(ext)]
    return name


class DavCollection(models.Model):
    _name = "dav.collection"
    _description = "A collection accessible via WebDAV"

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
            ("calendar", "Calendar"),
            ("addressbook", "Addressbook"),
            ("files", "Files"),
        ],
        string="Type",
        required=True,
        default="calendar",
    )
    tag = fields.Char(compute="_compute_tag")
    model_id = fields.Many2one(
        "ir.model",
        required=True,
        domain=[("transient", "=", False)],
        ondelete="cascade",
    )
    domain = fields.Char(
        required=True,
        default="[]",
    )
    field_uuid = fields.Many2one("ir.model.fields")
    field_mapping_ids = fields.One2many(
        "dav.collection.field_mapping",
        "collection_id",
        string="Field mappings",
    )
    url = fields.Char(compute="_compute_url")

    @api.depends("dav_type")
    def _compute_tag(self):
        """Compute DAV collection tag based on its type.

        Sets ``tag`` field to a DAV-specific container name:
          - ``VCALENDAR`` for calendar
          - ``VADDRESSBOOK`` for addressbook
          - False for files
        """
        for rec in self:
            if rec.dav_type == "calendar":
                rec.tag = "VCALENDAR"
            elif rec.dav_type == "addressbook":
                rec.tag = "VADDRESSBOOK"
            else:
                rec.tag = False

    def _compute_url(self):
        """Compute absolute DAV access URL for the collection.

        URL is constructed using:
          - system base URL
          - DAV prefix
          - current user login
          - collection ID
        """
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        ).rstrip("/")
        login = self.env.user.login or ""
        for rec in self:
            rec.url = (
                f"{base_url}{PREFIX}/{login}/{rec.id}"
                if base_url
                else f"{PREFIX}/{login}/{rec.id}"
            )

    @api.constrains("domain")
    def _check_domain(self):
        """Validate domain expression.

        Ensures that the stored domain string can be safely evaluated.

        :raises Exception: If domain evaluation fails
        """
        for rec in self:
            rec._eval_domain()

    @api.model
    def _eval_context(self):
        """Return safe evaluation context for domain expressions.

        :return: Dictionary containing allowed evaluation variables
        :rtype: Dict[str, Any]
        """
        return {
            "user": self.env.user,
        }

    def _eval_domain(self):
        """Evaluate stored domain expression into Odoo domain list.

        :raises ValueError: If domain string is invalid
        :return: Evaluated domain
        :rtype: List[Any]
        """
        self.ensure_one()
        return list(safe_eval(self.domain or "[]", self._eval_context()))

    def eval_domain_records(self):
        """Search records matching the evaluated domain.

        :return: Recordset of matching records
        :rtype: odoo.models.BaseModel
        """
        self.ensure_one()
        model_name = self.sudo().model_id.model
        return self.env[model_name].search(self._eval_domain())

    def get_record(self, components):
        """Retrieve record from path components.

        :param components: Parsed DAV path components
        :type components: Sequence[str]

        :return: Matching record or empty recordset
        :rtype: odoo.models.BaseModel
        """
        self.ensure_one()
        model_name = self.sudo().model_id.model
        collection_model = self.env[model_name]
        raw_key = components[-1] if components else ""
        key = _dav_strip_item_extension(raw_key)
        field_uuid = self.sudo().field_uuid
        if field_uuid:
            field_name = field_uuid.name
            if field_uuid.ttype in ("integer", "many2one"):
                try:
                    key = int(key)
                except (TypeError, ValueError):
                    return collection_model.browse()
        else:
            field_name = "id"
            try:
                key = int(key)
            except (TypeError, ValueError):
                return collection_model.browse()

        domain = expression.AND(
            [
                [(field_name, "=", key)],
                self._eval_domain(),
            ]
        )
        return collection_model.search(domain, limit=1)

    def _get_record_uid_value(self, record):
        """Return the DAV item identifier for a record.

        Uses ``field_uuid`` when configured, otherwise falls back to ``record.id``.
        The returned value matches the identifier format expected by
        :meth:`get_record`.
        """
        self.ensure_one()

        field_uuid = self.sudo().field_uuid
        if not field_uuid:
            return str(record.id)

        value = record[field_uuid.name]
        if field_uuid.ttype == "many2one":
            return str(value.id) if value else ""
        return str(value)

    def from_vobject(self, item):
        """Convert vobject item into Odoo field values.

        Supports:
          - VEVENT for calendar
          - VCARD for addressbook

        :param item: vobject instance
        :type item: Any

        :return: Dictionary of field values or None if unsupported
        :rtype: Optional[Dict[str, Any]]
        """
        self.ensure_one()

        if self.dav_type == "calendar":
            if item.name != "VCALENDAR" or not hasattr(item, "vevent"):
                return None
            item = item.vevent
        elif self.dav_type == "addressbook":
            if item.name != "VCARD":
                return None
        else:
            return None

        result = {}
        children = {c.name.lower(): c for c in item.getChildren()}
        for mapping in self.field_mapping_ids:
            field_id = mapping.sudo().field_id
            child = children.get(mapping.name.lower())
            if not child:
                continue
            value = mapping.from_vobject(child)
            if value is not None:
                result[field_id.name] = value
        return result

    def to_vobject(self, record):
        """Convert Odoo record into vobject representation.

        Automatically adds:
          - UID if missing
          - REV based on write_date

        :param record: Odoo record
        :type record: odoo.models.BaseModel

        :return: vobject instance or None for unsupported types
        :rtype: Optional[Any]
        """
        self.ensure_one()

        if self.dav_type == "calendar":
            result = vobject.iCalendar()
            vobj = result.add("vevent")
        elif self.dav_type == "addressbook":
            result = vobject.vCard()
            vobj = result
        else:
            return None

        for mapping in self.field_mapping_ids:
            value = mapping.to_vobject(record)
            if value is None or value is False:
                continue
            if isinstance(value, bool):
                continue
            if isinstance(value, (int | float)):
                value = str(value)
            vobj.add(mapping.name).value = value

        if "uid" not in vobj.contents:
            vobj.add("uid").value = self._get_record_uid_value(record)

        if (
            "rev" not in vobj.contents
            and "write_date" in record._fields
            and record.write_date
        ):
            s = fields.Datetime.to_string(record.write_date)  # YYYY-MM-DD HH:MM:SS
            vobj.add("rev").value = (
                s.replace("-", "").replace(" ", "T").replace(":", "") + "Z"
            )

        return result

    @api.model
    def _odoo_to_http_datetime(self, value):
        """Convert Odoo datetime to HTTP-date format (RFC 7231).

        :param value: Datetime value (string or datetime)
        :type value: Any

        :return: HTTP formatted datetime string or None
        :rtype: Optional[str]
        """
        if not value:
            return None
        if not isinstance(value, str):
            value = fields.Datetime.to_string(value)
        return time.strftime(
            "%a, %d %b %Y %H:%M:%S GMT",
            time.strptime(value, "%Y-%m-%d %H:%M:%S"),
        )

    @api.model
    def _split_path(self, path):
        """Split DAV path into normalized components.

        :param path: Raw path string
        :type path: Optional[str]

        :return: List of path segments
        :rtype: List[str]
        """
        return list(filter(None, posixpath.normpath(path or "").strip("/").split("/")))

    def dav_list(
        self,
        collection,
        path_components,
    ):
        """List DAV resources under given path.

        Handles:
          - file collections (attachments)
          - record-based collections (calendar/addressbook)

        :param collection: Radicale collection instance
        :type collection: Any
        :param path_components: Parsed DAV path
        :type path_components: Sequence[str]

        :return: List of resource href paths
        :rtype: List[str]
        """
        self.ensure_one()

        if self.dav_type == "files":
            if len(path_components) == 3:
                model_name = self.sudo().model_id.model
                collection_model = self.env[model_name]
                folder_name = unquote_plus(path_components[2])
                record = collection_model.browse(
                    map(
                        itemgetter(0),
                        collection_model.name_search(
                            folder_name,
                            operator="=",
                            limit=1,
                        ),
                    )
                )
                return [
                    "/"
                    + "/".join(path_components + [quote_plus(attachment.name or "")])
                    for attachment in self.env["ir.attachment"].search(
                        [
                            ("type", "=", "binary"),
                            ("res_model", "=", record._name),
                            ("res_id", "=", record.id),
                        ]
                    )
                ]
            elif len(path_components) == 2:
                return [
                    "/" + "/".join(path_components + [quote_plus(record.display_name)])
                    for record in self.eval_domain_records()
                ]

        if len(path_components) > 2:
            return []

        result = []
        for record in self.eval_domain_records():
            result.append(
                "/" + "/".join(path_components + [self._get_record_uid_value(record)])
            )
        return result

    def dav_delete(
        self,
        collection,
        href,
    ):
        """Delete DAV resource by href.

        :param collection: Radicale collection instance
        :type collection: Any
        :param href: Resource path
        :type href: str
        """
        self.ensure_one()

        if self.dav_type == "files":
            # TODO: Handle deletion of attachments
            return

        components = self._split_path(href)
        rec = self.get_record(components)
        if rec:
            rec.unlink()

    def dav_upload(self, collection, href, item):
        """Create or update DAV resource from uploaded vobject.

        :param collection: Radicale collection instance
        :type collection: Any
        :param href: Resource path
        :type href: str
        :param item: Uploaded vobject
        :type item: Any
        :raises AccessError: If created/updated record is outside collection domain
        :return: Radicale Item instance or None
        :rtype: Optional[Any]
        """
        self.ensure_one()

        if self.dav_type == "files":
            # TODO: Handle upload of attachments
            return None

        components = self._split_path(href)
        model_name = self.sudo().model_id.model
        collection_model = self.env[model_name]

        data = self.from_vobject(item)
        if not data:
            return None

        rec = self.get_record(components)
        if not rec:
            field_uuid = self.sudo().field_uuid
            if field_uuid:
                clean_key = _dav_strip_item_extension(
                    components[-1] if components else ""
                )
                if field_uuid.ttype in ("integer", "many2one"):
                    try:
                        clean_key = int(clean_key)
                    except (TypeError, ValueError):
                        clean_key = None
                if clean_key is not None and field_uuid.name not in data:
                    data[field_uuid.name] = clean_key

            rec = collection_model.create(data)
        else:
            rec.write(data)

        domain = expression.AND([self._eval_domain(), [("id", "=", rec.id)]])
        if not collection_model.search(domain, limit=1):
            raise AccessError(self.env._("Record is outside of DAV collection domain"))

        from ..radicale.collection import Item as DavItem

        return DavItem(
            collection,
            item=self.to_vobject(rec),
            href=href,
            last_modified=self._odoo_to_http_datetime(rec.write_date),
        )

    def dav_get(self, collection, href):
        """Retrieve DAV resource.

        Supports:
          - Folder access (files)
          - Attachment download
          - Calendar/addressbook items

        :param collection: Radicale collection instance
        :type collection: Any
        :param href: Resource path
        :type href: str

        :return: Radicale Item/FileItem/Collection or None
        :rtype: Optional[Any]
        """
        self.ensure_one()

        components = self._split_path(href)
        model_name = self.sudo().model_id.model
        collection_model = self.env[model_name]
        if self.dav_type == "files":
            if len(components) == 3:
                from ..radicale.collection import Collection as DavFolder

                folder = DavFolder(href)
                return folder

            if len(components) == 4:
                folder_name = unquote_plus(components[2])
                record = collection_model.browse(
                    map(
                        itemgetter(0),
                        collection_model.name_search(
                            folder_name,
                            operator="=",
                            limit=1,
                        ),
                    )
                )
                att_name = unquote_plus(components[3])
                attachment = self.env["ir.attachment"].search(
                    [
                        ("type", "=", "binary"),
                        ("res_model", "=", record._name),
                        ("res_id", "=", record.id),
                        ("name", "=", att_name),
                    ],
                    limit=1,
                )
                if not attachment:
                    return None

                from ..radicale.collection import FileItem

                return FileItem(
                    collection,
                    href,
                    attachment,
                    last_modified=self._odoo_to_http_datetime(record.write_date),
                )

        record = self.get_record(components)

        if not record:
            return None

        from ..radicale.collection import Item as DavItem

        return DavItem(
            collection,
            item=self.to_vobject(record),
            href=href,
            last_modified=self._odoo_to_http_datetime(record.write_date),
        )
