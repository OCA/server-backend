# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# How long change entries are kept before the daily cron discards them. A client
# offline for longer than this gets a 409 + valid-sync-token and re-lists, which
# is the RFC 6578 defined recovery.
RETENTION_DAYS = 90

# Opaque sync-token prefix. The shape is <prefix><collection id>-<change id>.
TOKEN_PREFIX = "http://dav.golder.lan/ns/sync/"


class DavSyncChange(models.Model):
    """Append-only log of changes inside a DAV collection.

    Sync-tokens are built from this table rather than from ``write_date``
    because a timestamp high-water mark cannot express a deletion.
    """

    _name = "dav.sync.change"
    _description = "Change log backing CalDAV/CardDAV sync-tokens"
    _order = "id asc"
    _rec_name = "id"

    collection_id = fields.Many2one(
        "dav.collection",
        string="Collection",
        required=True,
        ondelete="cascade",
        index=True,
    )
    model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True)
    dav_uid = fields.Char(
        help="DAV UID captured at the time of the change. Needed to report a "
        "deleted resource by its original href during a sync."
    )
    action = fields.Selection(
        [
            ("create", "Created"),
            ("write", "Updated"),
            ("unlink", "Deleted"),
        ],
        required=True,
    )
    create_date = fields.Datetime(readonly=True, index=True)

    # ------------------------------------------------------------------
    # Token handling
    # ------------------------------------------------------------------
    @api.model
    def current_ctag(self, collection):
        newest = self.sudo().search(
            [("collection_id", "=", collection.id)],
            limit=1,
            order="id desc",
        )
        return newest.id or 0

    @api.model
    def token_for(self, collection):
        """Return the newest valid sync-token for ``collection``."""
        return f"{TOKEN_PREFIX}{collection.id}-{self.current_ctag(collection)}"

    @api.model
    def parse_token(self, collection, token):
        """Return the change id encoded in ``token``, or None if unusable."""
        if not token or not token.startswith(TOKEN_PREFIX):
            return None
        raw = token[len(TOKEN_PREFIX):]
        collection_id, _, change_id = raw.partition("-")
        if not change_id.isdigit() or not collection_id.isdigit():
            return None
        if int(collection_id) != collection.id:
            return None
        return int(change_id)

    @api.model
    def changes_since(self, collection, change_id):
        return self.sudo().search(
            [
                ("collection_id", "=", collection.id),
                ("id", ">", change_id),
            ],
            order="id asc",
        )

    @api.model
    def token_is_usable(self, collection, change_id):
        """Whether a token can still be honoured.

        ``0`` is the legitimate baseline token of a collection that had not
        changed when the client last synced, and stays usable forever: it simply
        means "send me everything since the beginning". Only a token that is
        non-zero *and* older than the oldest retained row has fallen out of the
        retention window.
        """
        if change_id is None:
            return False
        if change_id == 0:
            return True
        oldest = self.sudo().search(
            [("collection_id", "=", collection.id)],
            limit=1,
            order="id asc",
        )
        if not oldest:
            # Nothing has ever changed; any token for this collection is fine.
            return True
        return change_id >= oldest.id

    @api.model
    def _cron_trim(self):
        cutoff = fields.Datetime.now() - timedelta(days=RETENTION_DAYS)
        stale = self.sudo().search([("create_date", "<", cutoff)])
        count = len(stale)
        if count:
            stale.unlink()
        return count


def log_changes(records, action):
    """Append one change entry per (collection, record) pair.

    Deliberately not filtered by the collection domain: over-logging only costs
    a client a redundant fetch, while under-logging silently strands a record
    on the device forever. The domain is applied when the REPORT is served.
    """
    if not records:
        return
    collections = records._dav_collections()
    if not collections:
        return
    change_model = records.env["dav.sync.change"].sudo()
    model_name = records._name
    values_list = [
        {
            "collection_id": collection.id,
            "model": model_name,
            "res_id": record.id,
            "dav_uid": record.dav_uid or str(record.id),
            "action": action,
        }
        for record in records
        for collection in collections
    ]
    change_model.create(values_list)
