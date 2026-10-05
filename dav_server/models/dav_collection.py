# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re

from odoo import api, fields, models
from odoo.exceptions import AccessDenied, AccessError, MissingError


class DavCollectionServer(models.Model):
    """Adds a stable, URL-safe handle and DAV-aware resolution helpers.

    Collections created by the scanner keep working: this module only adds the
    slug, and the files-only WebDAV endpoint is served by ``bureaucracy``.
    """

    _inherit = "dav.collection"

    dav_slug = fields.Char(
        string="DAV Slug",
        index=True,
        compute="_compute_dav_slug",
        store=True,
        help="Stable, URL-safe segment addressing this collection over DAV.",
    )

    @api.depends("name")
    def _compute_dav_slug(self):
        for collection in self:
            collection.dav_slug = self._unique_slug(collection)

    @api.model
    def _slugify(self, value):
        slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
        return slug or "collection"

    @api.model
    def _unique_slug(self, collection):
        base = self._slugify(collection.name)
        slug = base
        suffix = 2
        while self.sudo().with_context(active_test=False).search_count(
            [
                ("dav_slug", "=", slug),
                ("id", "not in", collection.ids),
            ]
        ):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    # ------------------------------------------------------------------
    # DAV resolution
    # ------------------------------------------------------------------
    @api.model
    def _dav_find_by_slug(self, slug, dav_type):
        collection = self.sudo().search(
            [("dav_slug", "=", slug), ("dav_type", "=", dav_type)],
            limit=1,
        )
        if not collection:
            return self.browse()
        return collection.with_user(self.env.user)

    @api.model
    def _dav_visible_collections(self, dav_type):
        """Collections of ``dav_type`` this user may see in their DAV home set.

        ``sudo`` is used only to enumerate the configuration; membership is
        decided by attempting to read a record from each collection under the
        requesting user's access rights.
        """
        result = self.browse()
        for collection in self.sudo().search([("dav_type", "=", dav_type)]):
            candidate = collection.with_user(self.env.user)
            if candidate._dav_user_can_read():
                result |= candidate
        return result

    def _dav_user_can_read(self):
        """Whether the current user can read this collection at all.

        ``AccessDenied`` (record rules) is a sibling of ``AccessError`` (ACLs),
        not a subclass, so both have to be caught for a portal user hitting the
        ``dav.collection`` ACL to be reported as "no access" rather than 500.

        This calls ``_dav_records`` rather than the inherited ``eval()``:
        ``eval`` resolves ``self.model_id.model`` under the current user, and an
        ordinary internal user is denied read access to ``ir.model``.
        """
        self.ensure_one()
        try:
            self._dav_records()
        except (AccessError, AccessDenied, MissingError):
            return False
        return True

    def _model_name(self):
        """The underlying model, read with ``sudo``.

        An ordinary internal user is denied read access to ``ir.model``, so
        resolving ``model_id.model`` under their rights raises and the whole
        collection looks empty. The model *name* is configuration, not user
        data; the records themselves are still read as the requesting user.
        """
        self.ensure_one()
        return self.sudo().model_id.model

    def _dav_records(self):
        """Records visible to the current user in this collection.

        The domain is evaluated with ``user`` bound to the authenticated DAV
        user, and the search runs under that user's access rights, so Odoo's
        record rules -- not the URL -- decide what a client can see.
        """
        self.ensure_one()
        model = self.env[self._model_name()]
        return model.search(self._eval_domain())

    def _dav_records_among(self, ids):
        self.ensure_one()
        model = self.env[self._model_name()]
        if not ids:
            return model.browse()
        return model.search([("id", "in", list(ids))] + self._eval_domain())

    def _dav_records_changed_since(self, change_rows):
        """Return ``(live_records, deleted_ids)`` for the given change rows."""
        self.ensure_one()
        live_ids = [row.res_id for row in change_rows if row.action != "unlink"]
        deleted_ids = [row.res_id for row in change_rows if row.action == "unlink"]
        return self._dav_records_among(live_ids), deleted_ids

    def _dav_record_by_uid(self, uid):
        """Find a record in this collection by its DAV UID, honouring rights."""
        self.ensure_one()
        model = self.env[self._model_name()]
        return model.search(
            self._eval_domain() + [("dav_uid", "=", uid)],
            limit=1,
        )

    def _dav_uid_field(self):
        """Name of the field carrying the DAV UID, if the model has one."""
        self.ensure_one()
        return "dav_uid" if "dav_uid" in self.sudo().model_id.fields_get() else "id"
