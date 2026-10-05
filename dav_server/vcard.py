# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Conversions between ``res.partner`` and vCard 3.0.

Uses ``vobject``, which is already a dependency of ``base_dav``. It emits
``VERSION:3.0``, which is what Thunderbird and DAVx5 negotiate, and handles
binary ``PHOTO`` encoding and multi-valued ``TEL``/``ADR`` for us.

The mapping is deliberately one-directional for bookkeeping: Odoo-managed
fields (``customer_rank``, ``write_uid``, ``commercial_partner_id``, ...) are
never populated from a device payload.
"""

import logging

import vobject
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)

TEXT_MAX = 100000

KIND_INDIVIDUAL = "individual"
KIND_GROUP = "group"

# res.partner.type -> vCard ADR TYPE parameter
ADDRESS_TYPES = {
    "contact": ["HOME"],
    "invoice": ["WORK"],
    "delivery": ["WORK"],
    "other": ["OTHER"],
}

# res.partner field -> vCard TEL TYPE parameter, in the order they are emitted
PHONE_TYPES = (
    ("phone", ("WORK", "VOICE")),
    ("mobile", ("CELL",)),
)

# Magic bytes -> vCard TYPE parameter for an embedded photo.
PHOTO_TYPES = (
    (b"\xff\xd8\xff", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"GIF87a", "GIF"),
    (b"GIF89a", "GIF"),
)


class UnsupportedPayload(ValueError):
    """The client sent something that cannot be represented in Odoo."""


# ======================================================================
# Export
# ======================================================================
def partner_to_vcard(partner):
    """Serialise a partner as a vCard 3.0 document."""
    card = vobject.vCard()
    card.add("fn").value = partner.display_name or partner.name or ""
    card.add("n").value = _structured_name(partner)
    card.add("uid").value = partner.dav_uid or str(partner.id)
    card.add("kind").value = KIND_GROUP if partner.is_company else KIND_INDIVIDUAL

    if partner.email:
        card.add("email").value = partner.email
    if partner.ref:
        card.add("nickname").value = partner.ref
    if partner.function:
        card.add("title").value = partner.function
    if partner.comment:
        card.add("note").value = _plain_text(partner.comment)

    organisation = partner.company_name or partner.parent_id.name
    if organisation:
        card.add("org").value = [organisation]
    if partner.title:
        card.add("role").value = partner.title.name

    for field, types in PHONE_TYPES:
        number = partner[field]
        if number:
            _add_typed(card, "tel", number, types)

    address = _postal_address(partner)
    if address:
        _add_typed(
            card, "adr", address, ADDRESS_TYPES.get(partner.type, ["OTHER"])
        )

    if partner.website:
        card.add("url").value = _normalise_url(partner.website)

    categories = sorted(
        category.display_name
        for category in partner.category_id
        if category.display_name
    )
    if categories:
        card.add("categories").value = categories

    photo = partner.image_1920
    if photo:
        prop = card.add("photo")
        prop.value = photo
        prop.params["ENCODING"] = ["b"]
        prop.params["TYPE"] = [_photo_type(photo)]
    return card.serialize()


def _add_typed(card, name, value, types):
    prop = card.add(name)
    prop.value = value
    prop.params["TYPE"] = list(types)
    return prop


def _structured_name(partner):
    """Best-effort split of Odoo's single ``name`` into family/given.

    Odoo stores one display string and neither Thai nor Chinese names split on
    the last space the way Latin names do, so anything without a clear Latin
    shape is carried entirely in ``given`` and still renders correctly.
    """
    raw = partner.name or ""
    parts = raw.split()
    if len(parts) < 2 or _has_cjk_or_thai(raw):
        return vobject.vcard.Name(family="", given=raw)
    return vobject.vcard.Name(family=parts[-1], given=" ".join(parts[:-1]))


def _has_cjk_or_thai(value):
    return any(
        "฀" <= character <= "๿"  # Thai
        or "一" <= character <= "鿿"  # CJK unified ideographs
        or "぀" <= character <= "ヿ"  # Kana
        or "가" <= character <= "힯"  # Hangul syllables
        for character in value
    )


def _postal_address(partner):
    if not any(
        (partner.street, partner.street2, partner.city, partner.zip, partner.country_id)
    ):
        return None
    return vobject.vcard.Address(
        box=partner.street2 or "",
        street=partner.street or "",
        city=partner.city or "",
        region=partner.state_id.code or partner.state_id.name or "",
        code=partner.zip or "",
        country=partner.country_id.code or partner.country_id.name or "",
    )


def _photo_type(data):
    for prefix, name in PHOTO_TYPES:
        if data.startswith(prefix):
            return name
    return "JPEG"


def _normalise_url(website):
    if not website:
        return ""
    if website.startswith(("http://", "https://")):
        return website
    return f"http://{website}"


def _plain_text(value):
    return html2plaintext(value or "")[:TEXT_MAX]


# ======================================================================
# Import
# ======================================================================
def vcard_to_partner_values(raw, user):
    """Turn a vCard payload into ``res.partner`` values."""
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
    try:
        card = vobject.readOne(text)
    except Exception as error:
        raise UnsupportedPayload(f"could not parse vCard: {error}") from error

    full_name = _full_name(card)
    if not full_name:
        raise UnsupportedPayload("vCard has no usable FN or N property")

    values = {
        "name": full_name[:TEXT_MAX],
        "ref": _single(card, "nickname") or False,
        "email": _email(card),
        "comment": _single(card, "note") or False,
        "is_company": _single(card, "kind", upper=True) == KIND_GROUP.upper(),
    }

    numbers = _telephone_numbers(card)
    if numbers.get("WORK"):
        values["phone"] = numbers["WORK"]
    if numbers.get("CELL"):
        values["mobile"] = numbers["CELL"]

    organisation = _organisation(card)
    if organisation:
        values["company_name"] = organisation

    title = _single(card, "title") or _single(card, "role")
    if title:
        values["function"] = title

    values.update(_address_values(card))

    url = _single(card, "url")
    if url:
        stripped = url.strip()
        if "://" in stripped:
            values["website"] = stripped.split("://", 1)[1]
        else:
            values["website"] = stripped

    categories = _categories(card)
    if categories:
        values["category_id"] = [(6, 0, _resolve_category_ids(user, categories))]
    return values


def _full_name(card):
    name = _single(card, "fn")
    if name:
        return name
    structured = card.contents.get("n")
    if not structured:
        return ""
    parts = structured[0].value
    joined = " ".join(
        piece for piece in (parts.given, parts.family) if piece
    ).strip()
    return joined


def _single(card, name, upper=False):
    entries = card.contents.get(name)
    if not entries:
        return ""
    value = entries[0].value
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value if item)
    text = str(value).strip()
    return text.upper() if upper else text


def _email(card):
    entries = card.contents.get("email") or []
    for entry in entries:
        value = str(entry.value or "").strip()
        if value and "@" in value:
            return value
    return False


def _telephone_numbers(card):
    """Pick one number per Odoo field, preferring the most specific TYPE."""
    found = {}
    fallback = None
    for entry in card.contents.get("tel") or []:
        value = str(entry.value or "").strip()
        if not value:
            continue
        types = _types(entry)
        if "CELL" in types and "CELL" not in found:
            found["CELL"] = value
        elif {"WORK", "VOICE"} & set(types) and "WORK" not in found:
            found["WORK"] = value
        elif "HOME" in types and "HOME" not in found:
            found["HOME"] = value
        elif fallback is None:
            fallback = value
    if fallback and not found:
        # Odoo has no "other phone" field; treat an untyped number as the
        # office line rather than dropping it.
        found["WORK"] = fallback
    return found


def _types(entry):
    values = entry.params.get("TYPE") or []
    if isinstance(values, str):
        values = [values]
    return [str(value).upper() for value in values]


def _organisation(card):
    entries = card.contents.get("org") or []
    if not entries:
        return ""
    value = entries[0].value
    if isinstance(value, (list, tuple)):
        return str(value[0]).strip() if value else ""
    return str(value).strip()


def _address_values(card):
    values = {}
    for entry in card.contents.get("adr") or []:
        types = _types(entry)
        if "WORK" not in types and "HOME" not in types:
            continue
        address = entry.value
        if address.street:
            values["street"] = address.street
        if address.box:
            values["street2"] = address.box
        if address.city:
            values["city"] = address.city
        if address.code:
            values["zip"] = address.code
        values["type"] = "contact" if "HOME" in types else "invoice"
        break
    return values


def _categories(card):
    entries = card.contents.get("categories") or []
    if not entries:
        return []
    value = entries[0].value
    if isinstance(value, str):
        value = [value]
    return [str(item).strip() for item in (value or []) if str(item).strip()]


def _resolve_category_ids(user, names):
    """Look up partner categories, creating the ones we do not have yet.

    Categories are plain labels with no record rules of their own, and the
    partner itself is still subject to ``res.partner`` access rules before this
    runs, so creating a missing label is low risk.
    """
    model = user.env["res.partner.category"].sudo()
    existing = model.search([("name", "in", names)])
    found = {category.name: category.id for category in existing}
    for name in names:
        if name not in found:
            found[name] = model.create({"name": name}).id
    return [found[name] for name in names if name in found]