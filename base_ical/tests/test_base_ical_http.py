# Copyright 2023 Hunki Enterprises BV
# Copyright 2024 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.tests.common import HttpCase


class TestBaseIcalHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls.env.ref("base_ical.demo_calendar")
        cls.user = cls.env.ref("base.user_demo")
        desc = (
            cls.env["base.ical.url.description"]
            .with_user(cls.user)
            .create({"calendar_id": cls.calendar.id, "name": "Testing"})
        )
        cls.calendar_url = desc._make_url()

    def test_calendar_retrieval(self):
        response = self.url_open(self.calendar_url)
        self.assertTrue(response.ok)
        self.assertTrue(response.text.startswith("BEGIN:VCALENDAR"))
