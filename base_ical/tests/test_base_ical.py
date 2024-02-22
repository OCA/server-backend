# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo.tests.common import Form, TransactionCase


class TestBaseIcal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env.ref("base_ical.demo_calendar")

    def test_profile(self):
        """Test url generation"""
        user = self.env.ref("base.user_demo")
        token_domain = [
            ("user_id", "=", user.id),
            ("ical_id", "=", self.calendar.id),
        ]
        token_search = (
            self.env["base.ical.token"].with_context(active_test=False).search
        )
        self.assertFalse(token_search(token_domain))
        self.assertFalse(self.calendar.with_user(user).user_active)
        self.calendar.with_user(user).action_enable()
        token = token_search(token_domain)
        self.assertTrue(token.active)
        self.calendar.invalidate_cache()
        self.assertTrue(self.calendar.with_user(user).user_active)
        self.calendar.with_user(user).action_disable()
        self.calendar.invalidate_cache()
        self.assertFalse(self.calendar.with_user(user).user_active)

    def test_config(self):
        """Configure calendar"""
        with Form(self.calendar) as calendar_form:
            calendar_form.model_id = self.env.ref("base.model_res_partner")
            self.assertFalse(calendar_form.expression_dtstart)
            self.assertFalse(calendar_form.preview)
            calendar_form.expression_dtstart = "record.create_date"
            calendar_form.expression_dtend = "record.write_date"
            self.assertTrue(calendar_form.preview)

    def test_auto_flag(self):
        """Test the auto flag is honored"""
        user = self.env.ref("base.user_demo")
        self.assertFalse(user.ical_token_ids)
        self.calendar.auto = True
        self.assertTrue(user.ical_token_ids)
        self.calendar.copy()
        self.assertEqual(len(user.ical_token_ids), 2)
        new_user = user.copy()
        self.assertEqual(len(new_user.ical_token_ids), 2)
