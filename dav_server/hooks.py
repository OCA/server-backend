# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models import dav_identity

_logger = logging.getLogger(__name__)

# Records that predate this module have no DAV UID. They are backfilled during
# installation so that hrefs are stable from the very first client sync.
MODELS_TO_BACKFILL = ("calendar.event", "res.partner")
BATCH_SIZE = 1000


def post_init_hook(env):
    for model_name in MODELS_TO_BACKFILL:
        _backfill_uids(env[model_name].sudo())


def _backfill_uids(records):
    while True:
        batch = records.with_context(active_test=False).search(
            [(dav_identity.UID_FIELD, "=", False)],
            limit=BATCH_SIZE,
        )
        if not batch:
            return
        _logger.info(
            "dav_server: assigning dav_uid to %d %s", len(batch), records._name
        )
        dav_identity.assign_uids(batch)
        if len(batch) < BATCH_SIZE:
            return
