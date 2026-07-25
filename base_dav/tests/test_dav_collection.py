# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.tests.common import TransactionCase

from .. import radicale
from ..radicale.auth import Auth


class TestDavCollection(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env["ir.model"]._get("res.partner")
        cls.collection = cls.env["dav.collection"].create(
            {
                "name": "Test Addressbook",
                "dav_type": "addressbook",
                "model_id": cls.partner_model.id,
                "domain": "[]",
            }
        )
        cls.name_field = cls.env["ir.model.fields"]._get("res.partner", "name")
        cls.mapping = cls.env["dav.collection.field_mapping"].create(
            {
                "collection_id": cls.collection.id,
                "name": "FN",
                "field_id": cls.name_field.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_compute_tag(self):
        self.assertEqual(self.collection.tag, "VADDRESSBOOK")
        calendar_model = self.env["ir.model"]._get("calendar.event")
        calendar_collection = self.env["dav.collection"].create(
            {
                "name": "Test Calendar",
                "dav_type": "calendar",
                "model_id": calendar_model.id,
                "domain": "[]",
            }
        )
        self.assertEqual(calendar_collection.tag, "VCALENDAR")

    def test_compute_url(self):
        self.assertIn("/.dav/", self.collection.url)
        self.assertTrue(self.collection.url.endswith("/%d" % self.collection.id))

    def test_eval_domain(self):
        self.assertEqual(self.collection._eval_domain(), [])
        self.collection.domain = "[('id', '=', %d)]" % self.partner.id
        self.assertIn(self.partner, self.collection.eval())

    def test_check_domain_invalid(self):
        with self.assertRaises((ValueError, SyntaxError)):
            self.collection.domain = "not a domain"
            self.collection.flush_recordset()

    def test_to_vobject_and_from_vobject(self):
        vobj = self.collection.to_vobject(self.partner)
        self.assertEqual(vobj.fn.value, self.partner.name)

        values = self.collection.from_vobject(vobj)
        self.assertEqual(values.get(self.name_field.name), self.partner.name)

    def test_dav_list_and_get(self):
        hrefs = self.collection.dav_list(None, ["admin", str(self.collection.id)])
        self.assertTrue(any(href.endswith("/%d" % self.partner.id) for href in hrefs))

        item = self.collection.dav_get(
            None, "/admin/%d/%d" % (self.collection.id, self.partner.id)
        )
        self.assertIsNotNone(item)


class TestDavAuth(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = "test_dav_password12345"
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Test DAV User",
                    "login": "test_dav_user",
                    "password": cls.password,
                    "email": "test_dav_user@example.com",
                }
            )
        )

    def _make_auth(self):
        return Auth.__new__(Auth)

    def test_login_success(self):
        fake_request = mock.Mock()
        fake_request.env = self.env
        fake_request.env.cr.dbname = self.env.cr.dbname
        with mock.patch.object(radicale.auth, "request", fake_request):
            auth = self._make_auth()
            result = auth._login(self.user.login, self.password)
        self.assertEqual(result, self.user.login)
        fake_request.update_env.assert_called_once()

    def test_login_wrong_password(self):
        fake_request = mock.Mock()
        fake_request.env = self.env
        fake_request.env.cr.dbname = self.env.cr.dbname
        with mock.patch.object(radicale.auth, "request", fake_request):
            auth = self._make_auth()
            result = auth._login(self.user.login, "wrong password")
        self.assertEqual(result, "")

    def test_login_missing_credentials(self):
        auth = self._make_auth()
        self.assertEqual(auth._login("", ""), "")
        self.assertEqual(auth._login(self.user.login, ""), "")
