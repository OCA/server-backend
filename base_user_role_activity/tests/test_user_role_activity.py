# Test for activity_update_role_reminder
from freezegun import freeze_time

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

ACTIVITY_XMLID = "base_user_role_activity.mail_activity_role_expire"


@tagged("post_install", "-at_install")
class TestActivityUpdateRoleReminder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Employee User",
                "login": "employee_user_role_activity",
            }
        )
        cls.partner = cls.user.partner_id

        cls.role = cls.env["res.users.role"].create({"name": "Test Role"})
        cls.role_2 = cls.env["res.users.role"].create({"name": "Test Role 2"})
        cls.role_line_1 = cls.env["res.users.role.line"].create(
            {
                "user_id": cls.user.id,
                "role_id": cls.role.id,
                "date_from": fields.Date.from_string("2024-01-01"),
                "date_to": fields.Date.from_string("2025-02-01"),
            }
        )
        cls.role_line_2 = cls.env["res.users.role.line"].create(
            {
                "user_id": cls.user.id,
                "role_id": cls.role_2.id,
                "date_from": fields.Date.from_string("2024-01-12"),
                "date_to": fields.Date.from_string("2025-01-12"),
            }
        )
        cls.activity_type = cls.env.ref(ACTIVITY_XMLID)

    @freeze_time("2025-01-01")
    def test_create_activity_when_expiring_lines(self):
        """Should create activity when expiring lines exist and no activity exists."""
        self.user.activity_update_role_reminder()
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertTrue(activities)

    @freeze_time("2025-01-01")
    def test_cleanup_activity_when_no_expiring_lines(self):
        """Should remove activity when no expiring lines exist."""
        self.user.activity_update_role_reminder()  # Create activity
        self.role_line_1.unlink()
        self.role_line_2.unlink()
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertFalse(activities)

    @freeze_time("2025-01-01")
    def test_no_update_needed_if_deadline_unchanged(self):
        """Should not update activity if deadline is unchanged."""
        self.user.activity_update_role_reminder()  # Create activity
        activities_before = self.partner.activity_search([ACTIVITY_XMLID])
        self.user.activity_update_role_reminder()  # Should not update
        activities_after = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertEqual(activities_before.ids, activities_after.ids)

    @freeze_time("2025-01-01")
    def test_update_activity_if_deadline_changed(self):
        """Should update activity if deadline changes."""
        self.user.activity_update_role_reminder()  # Create activity
        self.role_line_1.write({"date_to": fields.Date.from_string("2025-01-11")})
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertTrue(activities)
        self.assertEqual(
            activities[0].date_deadline, fields.Date.from_string("2025-01-11")
        )

    @freeze_time("2025-01-01")
    def test_no_duplicate_activity_for_same_deadline(self):
        """Should not create duplicate activities for same deadline."""
        self.user.activity_update_role_reminder()  # Create activity
        self.user.activity_update_role_reminder()  # Should not create duplicate
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertEqual(len(activities), 1)

    @freeze_time("2025-01-01")
    def test_no_duplicate_activity_when_done(self):
        """Should not create duplicate activities for same deadline."""
        self.user.activity_update_role_reminder()  # Create activity
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertEqual(len(activities), 1)
        activities.action_done()
        self.user.activity_update_role_reminder()  # Should not create duplicate
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertFalse(activities)

    @freeze_time("2024-12-09")
    def test_no_activity_for_before_reminder(self):
        """Should not create duplicate activities for same deadline."""
        self.user.activity_update_role_reminder()  # Create activity
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertFalse(activities)

    @freeze_time("2025-01-01")
    def test_activity_for_no_date_from(self):
        """Should not create duplicate activities for same deadline."""

        user_2 = self.env["res.users"].create(
            {
                "name": "Test User 2",
                "login": "testuser2",
            }
        )
        self.env["res.users.role.line"].create(
            {
                "user_id": user_2.id,
                "role_id": self.role.id,
                "date_to": fields.Date.from_string("2025-01-10"),
            }
        )
        user_2.activity_update_role_reminder()  # Create activity
        activities = user_2.partner_id.activity_search([ACTIVITY_XMLID])
        self.assertEqual(len(activities), 1)

    @freeze_time("2025-01-01")
    def test_activity_is_self_assigned_by_default(self):
        """The user is responsible for their own roles."""
        self.user.activity_update_role_reminder()
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertEqual(activities.user_id, self.user)

    def test_get_role_manager_default(self):
        """The hook returns the user itself by default."""
        self.assertEqual(self.user._get_role_manager(), self.user)
