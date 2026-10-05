# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDavUidMixin(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "DAV Tester",
                "login": "dav-tester",
                "email": "dav.tester@example.com",
            }
        )
        cls.collection = cls.env["dav.collection"].create(
            {
                "name": "Tester Calendar",
                "dav_type": "calendar",
                "model_id": cls.env["ir.model"]._get("calendar.event").id,
                "domain": "[]",
            }
        )

    def test_dav_uid_assigned_on_create(self):
        event = self.env["calendar.event"].create(
            {
                "name": "With UID",
                "start": "2026-01-05 09:00:00",
                "stop": "2026-01-05 10:00:00",
            }
        )
        self.assertTrue(event.dav_uid, "a DAV UID must be assigned on create")

    def test_dav_uid_survives_write(self):
        event = self._event()
        original = event.dav_uid
        event.write({"name": "Renamed"})
        self.assertEqual(event.dav_uid, original, "dav_uid must not change on write")

    def test_dav_slug_is_url_safe_and_unique(self):
        first = self.env["dav.collection"].create(
            {
                "name": "Family Calendar!",
                "dav_type": "calendar",
                "model_id": self.env["ir.model"]._get("calendar.event").id,
                "domain": "[]",
            }
        )
        second = self.env["dav.collection"].create(
            {
                "name": "family  calendar",
                "dav_type": "calendar",
                "model_id": self.env["ir.model"]._get("calendar.event").id,
                "domain": "[]",
            }
        )
        self.assertEqual(first.dav_slug, "family-calendar")
        self.assertEqual(second.dav_slug, "family-calendar-2")

    def test_change_log_records_create_write_unlink(self):
        changes = self.env["dav.sync.change"].sudo()
        before = changes.search_count(
            [("collection_id", "=", self.collection.id), ("res_id", "=", 0)]
        )
        event = self._event()
        actions = changes.search(
            [("collection_id", "=", self.collection.id), ("res_id", "=", event.id)]
        ).mapped("action")
        self.assertIn("create", actions)
        self.assertEqual(before, 0)

        event.write({"location": "Somewhere"})
        self.assertIn(
            "write",
            changes.search(
                [("collection_id", "=", self.collection.id), ("res_id", "=", event.id)]
            ).mapped("action"),
        )

        event.unlink()
        self.assertIn(
            "unlink",
            changes.search(
                [("collection_id", "=", self.collection.id), ("res_id", "=", event.id)]
            ).mapped("action"),
        )

    def test_unmapped_write_is_not_logged(self):
        event = self._event()
        changes = self.env["dav.sync.change"].sudo()
        baseline = changes.search_count(
            [("collection_id", "=", self.collection.id), ("res_id", "=", event.id)]
        )
        # ``write_uid`` is bookkeeping, not a DAV-mapped field.
        event.write({"write_uid": self.user.id})
        self.assertEqual(
            changes.search_count(
                [("collection_id", "=", self.collection.id), ("res_id", "=", event.id)]
            ),
            baseline,
        )

    def test_sync_token_round_trip(self):
        changes = self.env["dav.sync.change"].sudo()
        self._event()
        token = changes.token_for(self.collection)
        change_id = changes.parse_token(self.collection, token)
        self.assertIsNotNone(change_id)
        self.assertTrue(changes.token_is_usable(self.collection, change_id))
        self.assertIsNone(changes.parse_token(self.collection, "garbage"))
        self.assertIsNone(changes.parse_token(self.collection, ""))

    def test_collection_respects_record_rules(self):
        """A collection domain bound to another user must not leak."""
        other = self.env["res.users"].create(
            {
                "name": "Other Tester",
                "login": "dav-other-tester",
                "email": "other.tester@example.com",
            }
        )
        restricted = self.env["dav.collection"].create(
            {
                "name": "Someone Elses",
                "dav_type": "calendar",
                "model_id": self.env["ir.model"]._get("calendar.event").id,
                "domain": "[('user_id', '=', %d)]" % self.user.id,
            }
        )
        theirs = self.env["calendar.event"].create(
            {
                "name": "Theirs",
                "start": "2026-02-05 09:00:00",
                "stop": "2026-02-05 10:00:00",
                "user_id": self.user.id,
            }
        )
        mine = self.env["calendar.event"].create(
            {
                "name": "Not Mine",
                "start": "2026-02-06 09:00:00",
                "stop": "2026-02-06 10:00:00",
                "user_id": other.id,
            }
        )
        visible = restricted.with_user(self.user)._dav_records()
        self.assertIn(theirs, visible)
        self.assertNotIn(mine, visible)

    def test_portal_user_is_not_an_internal_user(self):
        """The controller gates on base.group_user; see TestDavProtocol."""
        portal = self.env["res.users"].create(
            {
                "name": "Portal",
                "login": "dav-portal",
                "email": "portal@example.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
        )
        self.assertFalse(portal.has_group("base.group_user"))
        self.assertTrue(self.user.has_group("base.group_user"))

    def _event(self):
        return self.env["calendar.event"].create(
            {
                "name": "Owned by Tester",
                "start": "2026-01-05 09:00:00",
                "stop": "2026-01-05 10:00:00",
                "user_id": self.user.id,
            }
        )
