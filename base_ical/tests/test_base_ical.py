# Copyright 2023 Hunki Enterprises BV
# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging
from urllib.parse import parse_qs, urlparse

import vobject

from odoo.tests.common import Form, TransactionCase

_logger = logging.getLogger(__name__)


class TestBaseIcal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env.ref("base_ical.demo_calendar")
        cls.user = cls.env.ref("base.user_demo")

    def test_profile(self):
        """Test url generation"""
        desc = (
            self.env["base.ical.url.description"]
            .with_user(self.user)
            .create({"calendar_id": self.calendar.id, "name": "Testing"})
        )

        url = desc._make_url()
        self.assertTrue(url)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        access_token = params.get("access_token")[0]
        self.assertTrue(access_token)

        user_id = self.env["res.users.apikeys"]._check_credentials(
            scope=f"odoo.plugin.ical.{self.calendar.id}",
            key=access_token,
        )
        self.assertEqual(user_id, self.user.id)

    def test_config_simple(self):
        """Configure a simple calendar"""
        with Form(self.calendar) as calendar_form:
            calendar_form.mode = "simple"
            calendar_form.model_id = self.env.ref("base.model_res_partner")
            self.assertFalse(calendar_form.expression_dtstart)
            self.assertFalse(calendar_form.preview)

            calendar_form.expression_dtstart = "record.create_date"
            calendar_form.expression_dtend = "record.write_date"
            self.assertTrue(calendar_form.preview)
            self.assertTrue(vobject.readOne(calendar_form.preview))

    def test_config_advanced_event(self):
        with Form(self.calendar) as calendar_form:
            calendar_form.mode = "advanced"
            calendar_form.model_id = self.env.ref("base.model_res_partner")
            self.assertFalse(calendar_form.preview)

            calendar_form.code = (
                "event = {"
                "'dtstart':record.create_date,"
                "'dtend':record.write_date,"
                "'summary':record.name,"
                "}"
            )
            self.assertTrue(calendar_form.preview)
            cal = vobject.readOne(calendar_form.preview)
            self.assertTrue(cal)
            self.assertTrue(
                any(item.name.lower() == "vevent" for item in cal.getChildren())
            )

    def test_config_advanced_todo(self):
        with Form(self.calendar) as calendar_form:
            calendar_form.mode = "advanced"
            calendar_form.model_id = self.env.ref("base.model_res_partner")
            self.assertFalse(calendar_form.preview)
            calendar_form.code = (
                "todo = {'due':record.write_date,'summary':record.name}"
            )
            self.assertTrue(calendar_form.preview)
            cal = vobject.readOne(calendar_form.preview)
            self.assertTrue(cal)
            self.assertTrue(
                any(item.name.lower() == "vtodo" for item in cal.getChildren())
            )

    def test_config_advanced_calendar(self):
        code = (
            "cal = vobject.iCalendar()\n"
            "dict2ical(cal.add('vevent'),{"
            "'summary':record.name,"
            "'dtstart':record.create_date,"
            "'dtend':record.write_date})\n"
        )
        with Form(self.calendar) as calendar_form:
            calendar_form.mode = "advanced"
            calendar_form.model_id = self.env.ref("base.model_res_partner")
            self.assertFalse(calendar_form.preview)
            calendar_form.code = (
                code + "calendar = {record.id:cal.serialize().encode()}"
            )
            self.assertTrue(calendar_form.preview)
            cal = vobject.readOne(calendar_form.preview)
            self.assertTrue(cal)

    def test_auto_flag(self):
        """Test the auto flag is honored"""
        self.assertFalse(self.calendar.allowed_users_ids)

        self.calendar.auto = True
        self.assertTrue(self.calendar.allowed_users_ids)
        new_calendar = self.calendar.copy()
        self.assertIn(self.user, new_calendar.allowed_users_ids)

        self.calendar.auto = False
        new_user = self.user.copy()
        self.assertNotIn(new_user, self.calendar.allowed_users_ids)

        self.calendar.auto = True
        new_user = new_user.copy()
        self.assertIn(new_user, self.calendar.allowed_users_ids)
