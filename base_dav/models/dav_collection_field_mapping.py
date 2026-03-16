# Copyright 2019 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import binascii
import datetime
import re as re_mod

import dateutil
import vobject
from dateutil import tz

from odoo import api, fields, models, tools
from odoo.tools import safe_eval as safe_eval_mod


def _safe_module(name, fallback_module, attributes_tree):
    """Return safe_eval-wrapped module or fallback module.

    If a module with the given name is already pre-wrapped inside
    ``safe_eval``, it is returned. Otherwise, the fallback module
    is wrapped using the provided attribute tree.

    :param name: Module name to look up inside safe_eval
    :type name: str
    :param fallback_module: Python module used if not prewrapped
    :type fallback_module: Any
    :param attributes_tree: Allowed attributes structure
    :type attributes_tree: Dict[str, Any]

    :return: Safe wrapped module proxy
    :rtype: Any
    """
    prewrapped = getattr(safe_eval_mod, name, None)
    if prewrapped is not None:
        return prewrapped
    return safe_eval_mod.wrap_module(fallback_module, attributes_tree)


SAFE_DATETIME = _safe_module(
    "datetime",
    datetime,
    {
        "date": {},
        "datetime": {},
        "time": {},
        "timedelta": {},
    },
)

SAFE_DATEUTIL = _safe_module(
    "dateutil",
    dateutil,
    {
        "tz": {},
    },
)

SAFE_TZ = _safe_module(
    "tz",
    tz,
    {
        "UTC": {},
        "gettz": {},
    },
)

SAFE_VOBJECT = _safe_module(
    "vobject",
    vobject,
    {
        "vCard": {},
        "iCalendar": {},
        "vcard": {"Name": {}},
        "base": {},
    },
)


class DavCollectionFieldMapping(models.Model):
    _name = "dav.collection.field_mapping"
    _description = "A field mapping for a WebDAV collection"

    collection_id = fields.Many2one(
        comodel_name="dav.collection",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(
        required=True,
        help="Attribute name in the vobject",
    )
    mapping_type = fields.Selection(
        [
            ("simple", "Simple"),
            ("code", "Code"),
        ],
        default="simple",
        required=True,
    )
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        required=True,
        ondelete="cascade",
        help="Field of the model the values are mapped to",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        related="collection_id.model_id",
    )
    import_code = fields.Text(
        help="Code to import the value from a vobject. Use the variable "
        "result for the output of the value and item as input"
    )
    export_code = fields.Text(
        help="Code to export the value to a vobject. Use the variable "
        "result for the output of the value and record as input"
    )

    def from_vobject(self, child):
        """Convert vobject child element into Odoo field value.

        Delegates conversion depending on mapping type:
          - simple
          - code

        :param child: vobject child element
        :type child: Any

        :return: Converted field value
        :rtype: Any
        """
        self.ensure_one()
        if self.mapping_type == "code":
            return self._from_vobject_code(child)
        return self._from_vobject_simple(child)

    def _from_vobject_code(self, child):
        """Convert vobject child using custom Python code.

        Executes safe_eval code stored in ``import_code``.
        The following variables are available:
          - item
          - result
          - datetime
          - dateutil
          - tz
          - vobject

        :param child: vobject child element
        :type child: Any

        :return: Converted value stored in ``result``
        :rtype: Any
        """
        self.ensure_one()
        context = {
            "item": child,
            "result": None,
            "datetime": SAFE_DATETIME,
            "dateutil": SAFE_DATEUTIL,
            "tz": SAFE_TZ,
            "vobject": SAFE_VOBJECT,
            "DEFAULT_SERVER_DATE_FORMAT": tools.DEFAULT_SERVER_DATE_FORMAT,
            "DEFAULT_SERVER_DATETIME_FORMAT": tools.DEFAULT_SERVER_DATETIME_FORMAT,
        }
        safe_eval_mod.safe_eval(
            self.import_code or "", context, mode="exec", nocopy=True
        )
        return context.get("result", None)

    def _from_vobject_simple(self, child):
        """Convert vobject child using automatic type-based mapping.

        Attempts conversion based on field type and attribute name.

        :param child: vobject child element
        :type child: Any

        :return: Converted value
        :rtype: Any
        """
        self.ensure_one()
        name = (self.name or "").lower()
        conversion_funcs = [
            f"_from_vobject_{self.field_id.ttype}_{name}",
            f"_from_vobject_{self.field_id.ttype}",
        ]

        for conversion_func in conversion_funcs:
            if hasattr(self, conversion_func):
                value = getattr(self, conversion_func)(child)
                if value is not None:
                    return value

        return child.value

    @api.model
    def _from_vobject_datetime(self, item):
        """Convert vobject datetime into Odoo datetime string (UTC).

        :param item: vobject datetime property
        :type item: Any

        :return: Datetime string in server format or None
        :rtype: Optional[str]
        """
        if isinstance(item.value, datetime.datetime):
            value = item.value.astimezone(dateutil.tz.UTC)
            return value.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        if isinstance(item.value, datetime.date):
            return item.value.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        return None

    @api.model
    def _from_vobject_date(self, item):
        """Convert vobject date into Odoo date string.

        :param item: vobject date property
        :type item: Any

        :return: Date string in server format or None
        :rtype: Optional[str]
        """
        if isinstance(item.value, datetime.datetime):
            value = item.value.astimezone(dateutil.tz.UTC)
            return value.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        if isinstance(item.value, datetime.date):
            return item.value.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        return None

    @api.model
    def _from_vobject_binary(self, item):
        """Convert vobject binary value into ASCII-encoded bytes.

        :param item: vobject binary property
        :type item: Any

        :return: ASCII-encoded bytes
        :rtype: bytes
        """
        value = getattr(item, "value", None)
        if not value:
            return None
        if isinstance(value, str):
            raw = value.encode("ascii", errors="ignore")
        elif isinstance(value, bytes):
            raw = value
        else:
            raw = bytes(value)
        if raw.startswith(
            (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"BM")
        ):
            return base64.b64encode(raw)
        compact = b"".join(raw.split())
        try:
            decoded = base64.b64decode(compact, validate=True)
            return base64.b64encode(decoded)
        except (binascii.Error, ValueError):
            return base64.b64encode(raw)

    @api.model
    def _from_vobject_char_n(self, item):
        """Extract family name from vCard Name object.

        :param item: vobject Name property
        :type item: Any

        :return: Family name or None
        :rtype: Optional[str]
        """
        value = getattr(item, "value", None)
        if hasattr(value, "family"):
            return value.family
        if isinstance(value, str):
            return value.split(";", 1)[0] or None
        return None

    def to_vobject(self, record):
        """Convert Odoo record value into vobject-compatible value.

        Delegates conversion depending on mapping type.
        Ensures timezone awareness for datetime values.

        :param record: Odoo record
        :type record: odoo.models.BaseModel

        :return: Value suitable for vobject property
        :rtype: Any
        """
        self.ensure_one()
        if self.mapping_type == "code":
            result = self._to_vobject_code(record)
        else:
            result = self._to_vobject_simple(record)

        if isinstance(result, datetime.datetime) and not result.tzinfo:
            return result.replace(tzinfo=tz.UTC)
        return result

    def _to_vobject_code(self, record):
        """Convert Odoo record value using custom export code.

        Executes safe_eval code stored in ``export_code``.

        :param record: Odoo record
        :type record: odoo.models.BaseModel

        :return: Converted value stored in ``result``
        :rtype: Any
        """
        self.ensure_one()
        context = {
            "record": record,
            "result": None,
            "datetime": SAFE_DATETIME,
            "dateutil": SAFE_DATEUTIL,
            "tz": SAFE_TZ,
            "vobject": SAFE_VOBJECT,
            "re": safe_eval_mod.wrap_module(
                re_mod, {"sub": {}, "match": {}, "search": {}, "compile": {}}
            ),
            "DEFAULT_SERVER_DATE_FORMAT": tools.DEFAULT_SERVER_DATE_FORMAT,
            "DEFAULT_SERVER_DATETIME_FORMAT": tools.DEFAULT_SERVER_DATETIME_FORMAT,
        }
        safe_eval_mod.safe_eval(
            self.export_code or "", context, mode="exec", nocopy=True
        )
        return context.get("result", None)

    def _to_vobject_simple(self, record):
        """Convert Odoo field value using automatic type-based mapping.

        :param record: Odoo record
        :type record: odoo.models.BaseModel

        :return: Converted value
        :rtype: Any
        """
        self.ensure_one()
        conversion_funcs = [
            f"_to_vobject_{self.field_id.ttype}_{(self.name or '').lower()}",
            f"_to_vobject_{self.field_id.ttype}",
        ]
        value = record[self.field_id.name]
        for conversion_func in conversion_funcs:
            if hasattr(self, conversion_func):
                return getattr(self, conversion_func)(value)
        if value is False:
            return None
        return value

    @api.model
    def _to_vobject_datetime(self, value):
        """Convert Odoo datetime value into UTC datetime object.

        :param value: Odoo datetime value
        :type value: Any

        :return: Timezone-aware datetime or None
        :rtype: Optional[datetime.datetime]
        """
        dt = fields.Datetime.to_datetime(value)
        return dt.replace(tzinfo=tz.UTC) if dt else None

    @api.model
    def _to_vobject_datetime_rev(self, value):
        """Convert Odoo datetime into REV string format (RFC-style).

        :param value: Odoo datetime value
        :type value: Any

        :return: REV formatted string or None
        :rtype: Optional[str]
        """
        s = fields.Datetime.to_string(value) if value else None
        return s and s.replace("-", "").replace(" ", "T").replace(":", "") + "Z"

    @api.model
    def _to_vobject_date(self, value):
        """Convert Odoo date value into date object.

        :param value: Odoo date value
        :type value: Any

        :return: Date object or None
        :rtype: Optional[datetime.date]
        """
        return fields.Date.to_date(value)

    @api.model
    def _to_vobject_binary(self, value):
        """Convert binary field value into ASCII string.

        :param value: Binary value
        :type value: Optional[bytes]

        :return: ASCII-decoded string or None
        :rtype: Optional[str]
        """
        return value and value.decode("ascii")

    @api.model
    def _to_vobject_char_n(self, value):
        """Convert family name into vCard Name object.

        :param value: Family name
        :type value: Optional[str]

        :return: vobject.vcard.Name instance
        :rtype: Any
        """
        # TODO: how are we going to handle compound types like this?
        return vobject.vcard.Name(family=value)
