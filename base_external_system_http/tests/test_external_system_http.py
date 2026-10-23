# Copyright 2026 Therp BV.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from ..models import external_system_adapter_http as http_mod


class _FakeResponse:
    __slots__ = ("status_code", "text")

    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text


class TestExternalSystemHTTP(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.system = cls.env.ref("base_external_system_http.external_system_github")

    def _make_variant_system(self, **overrides):
        """Create a minimal external.system record for isolated tests"""
        vals = {
            "name": "HTTP Test System (variant)",
            "system_type": "external.system.adapter.http",
            "host": "github.com",
            "remote_path": "/OCA",
            "company_ids": [(6, 0, [self.env.company.id])],
        }
        vals.update(overrides)
        return self.env["external.system"].create(vals)

    def test_get_http_adapter(self):
        adapter_model = self.env["external.system.adapter.http"]
        self.assertIn(
            (adapter_model._name, adapter_model._description),
            self.env["external.system"]._get_system_types(),
        )

    def test_interface(self):
        self.assertTrue(self.system.interface)
        self.assertEqual(
            self.system.interface._name,
            "external.system.adapter.http",
        )
        self.assertEqual(self.system.interface.system_id, self.system)

    def test_get_base_url_and__response(self):
        with patch.object(http_mod.requests, "get") as mock_get:
            mock_get.return_value = _FakeResponse(status_code=200, text="<head>")
            with self.system.client() as client:
                response = client.get()
            mock_get.assert_called()
            called_url = mock_get.call_args[0][0]
            self.assertTrue(called_url.startswith("https://github.com"))
            self.assertIn("/OCA", called_url)
            self.assertIn("<head>", response.text)

    def test_get_with_endpoint(self):
        with patch.object(http_mod.requests, "get") as mock_get:
            mock_get.return_value = _FakeResponse(status_code=200, text="server-tools")

            with self.system.client() as client:
                response = client.get(endpoint="tools")

            called_url = mock_get.call_args[0][0]
            self.assertIn("/server-tools", called_url)
            self.assertIn("server-tools", response.text)

    def test_get_http_error(self):
        with patch.object(http_mod.requests, "get") as mock_get:
            mock_get.return_value = _FakeResponse(status_code=500, text="boom")
            with self.assertRaises(ValidationError):
                with self.system.client() as client:
                    client.get()

    def test_get_request_exception(self):
        with patch.object(
            http_mod.requests,
            "get",
            side_effect=http_mod.req_exc.RequestException("network down"),
        ):
            with self.assertRaises(ValidationError):
                with self.system.client() as client:
                    client.get()

    def test_post_response(self):
        with patch.object(http_mod.requests, "post") as mock_post:
            mock_post.return_value = _FakeResponse(status_code=200, text="ok")
            with self.system.client() as client:
                response = client.post()
            mock_post.assert_called()
            called_url = mock_post.call_args[0][0]
            self.assertTrue(called_url.startswith("https://github.com"))
            self.assertIn("/OCA", called_url)
            self.assertIn("ok", response.text)

    def test_post_with_endpoint(self):
        with patch.object(http_mod.requests, "post") as mock_post:
            mock_post.return_value = _FakeResponse(status_code=200, text="server-tools")
            with self.system.client() as client:
                response = client.post(endpoint="tools")
            called_url = mock_post.call_args[0][0]
            self.assertIn("/server-tools", called_url)
            self.assertIn("server-tools", response.text)

    def test_post_http_error(self):
        with patch.object(http_mod.requests, "post") as mock_post:
            mock_post.return_value = _FakeResponse(status_code=500, text="boom")
            with self.assertRaises(ValidationError):
                with self.system.client() as client:
                    client.post()

    def test_put_response(self):
        with patch.object(http_mod.requests, "put") as mock_put:
            mock_put.return_value = _FakeResponse(status_code=200, text="ok")

            with self.system.client() as client:
                response = client.put()
            mock_put.assert_called()
            called_url = mock_put.call_args[0][0]
            self.assertTrue(called_url.startswith("https://github.com"))
            self.assertIn("/OCA", called_url)
            self.assertIn("ok", response.text)

    def test_put_with_endpoint(self):
        with patch.object(http_mod.requests, "put") as mock_put:
            mock_put.return_value = _FakeResponse(status_code=200, text="server-tools")
            with self.system.client() as client:
                response = client.put(endpoint="tools")
            called_url = mock_put.call_args[0][0]
            self.assertIn("/server-tools", called_url)
            self.assertIn("server-tools", response.text)

    def test_put_http_error(self):
        with patch.object(http_mod.requests, "put") as mock_put:
            mock_put.return_value = _FakeResponse(status_code=500, text="boom")
            with self.assertRaises(ValidationError):
                with self.system.client() as client:
                    client.put()

    def test_delete_response(self):
        with patch.object(http_mod.requests, "delete") as mock_delete:
            mock_delete.return_value = _FakeResponse(status_code=200, text="ok")
            with self.system.client() as client:
                response = client.delete()
            mock_delete.assert_called()
            called_url = mock_delete.call_args[0][0]
            self.assertTrue(called_url.startswith("https://github.com"))
            self.assertIn("/OCA", called_url)
            self.assertIn("ok", response.text)

    def test_delete_with_endpoint(self):
        with patch.object(http_mod.requests, "delete") as mock_delete:
            mock_delete.return_value = _FakeResponse(
                status_code=200, text="server-tools"
            )
            with self.system.client() as client:
                response = client.delete(endpoint="tools")
            called_url = mock_delete.call_args[0][0]
            self.assertIn("/server-tools", called_url)
            self.assertIn("server-tools", response.text)

    def test_delete_http_error(self):
        with patch.object(http_mod.requests, "delete") as mock_delete:
            mock_delete.return_value = _FakeResponse(status_code=500, text="boom")
            with self.assertRaises(ValidationError):
                with self.system.client() as client:
                    client.delete()

    def test_get_url(self):
        sys = self._make_variant_system(
            name="HTTP Test System (https host)",
            host="https://github.com",
        )
        with sys.client() as client:
            url = client._get_url()
        self.assertTrue(url.startswith("https://github.com"))
        sys2 = self._make_variant_system(
            name="HTTP Test System (http host)",
            host="http://github.com",
        )
        with sys2.client() as client:
            url2 = client._get_url()
        self.assertTrue(url2.startswith("http://github.com"))

    def test_action_test_connection(self):
        with patch.object(http_mod.requests, "get") as mock_get:
            mock_get.return_value = _FakeResponse(status_code=200, text="ok")
            with self.assertRaises(UserError):
                self.system.action_test_connection()
