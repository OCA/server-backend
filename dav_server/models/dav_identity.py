# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Shared behaviour for models exposed through a DAV collection.

This is deliberately a module of plain functions rather than an Odoo
``AbstractModel``. Two alternatives were tried and both fail:

* Putting an ``AbstractModel`` in ``_inherit`` *alongside* a concrete model
  (``_inherit = ["calendar.event", "dav.uid.mixin"]``) makes Odoo build that
  model's field set twice. Registry setup then aborts with ``Many2many fields
  DavCalendarEvent.categ_ids and calendar.event.categ_ids use the same table and
  columns``.
* A plain Python mixin does not work either: Odoo's field descriptors assert
  ``issubclass(owner, BaseModel)`` in ``__set_name__``.

So each concrete model declares its own ``dav_uid`` field and its own
create/write/unlink overrides, and they delegate here.
"""

import uuid

UID_FIELD = "dav_uid"


def new_uid():
    return uuid.uuid4().hex


def assign_uids(records):
    """Give every record in ``records`` that lacks one a fresh DAV UID."""
    for record in records:
        if not record[UID_FIELD]:
            record[UID_FIELD] = new_uid()


def collections_for(records):
    """Non-files DAV collections pointing at ``records``' model."""
    Collection = records.env["dav.collection"]
    if not records:
        return Collection.browse()
    return Collection.sudo().search(
        [
            ("model_id.model", "=", records._name),
            ("dav_type", "!=", "files"),
        ]
    )


def log_changes(records, action):
    """Append one change entry per (collection, record) pair.

    Deliberately not filtered by the collection domain: over-logging only costs
    a client a redundant fetch, while under-logging silently strands a record on
    the device forever. The domain is applied when the change REPORT is served.
    """
    if not records:
        return
    collections = collections_for(records)
    if not collections:
        return
    change_model = records.env["dav.sync.change"].sudo()
    model_name = records._name
    change_model.create(
        [
            {
                "collection_id": collection.id,
                "model": model_name,
                "res_id": record.id,
                "dav_uid": record[UID_FIELD] or str(record.id),
                "action": action,
            }
            for record in records
            for collection in collections
        ]
    )


def uid_of(record):
    """The stable DAV UID of a record, falling back to its id."""
    return record[UID_FIELD] or str(record.id)