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
        # Multi-company dataset for manager selection tests
        cls.company_a = cls.env["res.company"].create({"name": "Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})

        cls.manager_user_a = cls.env["res.users"].create(
            {
                "name": "Manager A",
                "login": "manager_a_role_activity",
                "company_id": cls.company_a.id,
                "company_ids": [fields.Command.set([cls.company_a.id])],
            }
        )
        cls.manager_user_b = cls.env["res.users"].create(
            {
                "name": "Manager B",
                "login": "manager_b_role_activity",
                "company_id": cls.company_b.id,
                "company_ids": [fields.Command.set([cls.company_b.id])],
            }
        )

        cls.user = cls.env["res.users"].create(
            {
                "name": "Employee User",
                "login": "employee_user_role_activity",
                "company_id": cls.company_a.id,
                "company_ids": [
                    fields.Command.set([cls.company_a.id, cls.company_b.id])
                ],
            }
        )
        cls.partner = cls.user.partner_id

        cls.manager_employee_a = cls.env["hr.employee"].create(
            {
                "name": "Manager Employee A",
                "user_id": cls.manager_user_a.id,
                "company_id": cls.company_a.id,
            }
        )
        cls.manager_employee_b = cls.env["hr.employee"].create(
            {
                "name": "Manager Employee B",
                "user_id": cls.manager_user_b.id,
                "company_id": cls.company_b.id,
            }
        )

        cls.employee_in_a = cls.env["hr.employee"].create(
            {
                "name": "Employee in A",
                "user_id": cls.user.id,
                "company_id": cls.company_a.id,
                "parent_id": cls.manager_employee_a.id,
            }
        )
        cls.employee_in_b = cls.env["hr.employee"].create(
            {
                "name": "Employee in B",
                "user_id": cls.user.id,
                "company_id": cls.company_b.id,
                "parent_id": cls.manager_employee_b.id,
            }
        )

        cls.role = cls.env["res.users.role"].create(
            {
                "name": "Test Role",
            }
        )
        cls.role_2 = cls.env["res.users.role"].create(
            {
                "name": "Test Role 2",
            }
        )
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

    def _get_activities(self):
        return self.user.partner_id.activity_search([ACTIVITY_XMLID])

    def _cleanup_activities(self):
        self._get_activities().unlink()

    # ------------------------------------------------------------------
    # tests
    # ------------------------------------------------------------------

    @freeze_time("2025-01-15")
    def test_manager_from_current_company_is_assigned(self):
        """Activity user_id should be Manager A when env.company is Company A."""
        self._cleanup_activities()
        env_a = self.env(
            context=dict(self.env.context, allowed_company_ids=[self.company_a.id])
        )
        env_a["res.users"].browse(self.user.id).activity_update_role_reminder()

        activities = self._get_activities()
        self.assertTrue(activities, "An activity should have been created")
        self.assertEqual(
            activities[0].user_id,
            self.manager_user_a,
            "Activity should be assigned to Manager A (current company)",
        )

    @freeze_time("2025-01-15")
    def test_fallback_to_other_company_manager(self):
        """When env.company has no matching employee, fall back to first found."""
        self._cleanup_activities()
        # Use a third company that user has no employee record in
        company_c = self.env["res.company"].create({"name": "Company C (no employee)"})
        env_c = self.env(
            context=dict(self.env.context, allowed_company_ids=[company_c.id])
        )
        env_c["res.users"].browse(self.user.id).activity_update_role_reminder()

        activities = self._get_activities()
        self.assertTrue(activities, "An activity should have been created")
        # Fallback: first employee found is in Company A (earlier creation order)
        self.assertIn(
            activities[0].user_id,
            self.manager_user_a | self.manager_user_b,
            "Activity should fall back to one of the existing managers",
        )

    @freeze_time("2025-01-15")
    def test_preferred_company_b_manager_when_env_is_company_b(self):
        """Activity user_id should be Manager B when env.company is Company B."""
        self._cleanup_activities()
        env_b = self.env(
            context=dict(self.env.context, allowed_company_ids=[self.company_b.id])
        )
        env_b["res.users"].browse(self.user.id).activity_update_role_reminder()

        activities = self._get_activities()
        self.assertTrue(activities, "An activity should have been created")
        self.assertEqual(
            activities[0].user_id,
            self.manager_user_b,
            "Activity should be assigned to Manager B (current company)",
        )

    @freeze_time("2025-01-15")
    def test_no_manager_falls_back_to_user(self):
        # When user has no employee records with a parent, activity is self-assigned.
        self._cleanup_activities()
        # Create a user with no hr.employee record
        standalone_user = self.env["res.users"].create(
            {
                "name": "Standalone User",
                "login": "standalone_role_activity",
                "company_id": self.company_a.id,
                "company_ids": [fields.Command.set([self.company_a.id])],
            }
        )
        role_line = self.env["res.users.role.line"].create(
            {
                "user_id": standalone_user.id,
                "role_id": self.role.id,
                "date_from": fields.Date.from_string("2024-01-01"),
                "date_to": fields.Date.from_string("2025-02-01"),
            }
        )
        try:
            standalone_user.activity_update_role_reminder()
            activities = standalone_user.partner_id.activity_search([ACTIVITY_XMLID])
            self.assertTrue(activities, "An activity should have been created")
            self.assertEqual(
                activities[0].user_id,
                standalone_user,
                "Activity should be self-assigned when no manager exists",
            )
        finally:
            role_line.unlink()
            standalone_user.partner_id.activity_search([ACTIVITY_XMLID]).unlink()

    @freeze_time("2025-01-01")
    def test_cron_role_reminder_creates_activity(self):
        """Cron path uses .search() instead of filtered_domain and creates reminder."""
        self._cleanup_activities()
        self.env["res.users.role.line"].cron_role_reminder()
        activities = self.partner.activity_search([ACTIVITY_XMLID])
        self.assertTrue(activities)
