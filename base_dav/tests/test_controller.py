# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace
from unittest import mock

from odoo import http
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base_dav.controllers.main import PREFIX, Main


class _ClosableResult(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False

    def close(self):
        self.closed = True


@tagged("post_install", "-at_install")
class TestDavController(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = Main()

    def _push_request(self, method="PROPFIND", body=b"", environ=None):
        httprequest = SimpleNamespace(
            environ=environ or {"REQUEST_METHOD": method},
            method=method,
            get_data=lambda cache=False: body,
        )
        req = SimpleNamespace(
            httprequest=httprequest,
            env=self.env,
            uid=self.env.uid,
        )
        http._request_stack.push(req)
        self.addCleanup(http._request_stack.pop)

    def test_handle_dav_request_preserves_empty_propfind_body(self):
        self._push_request(method="PROPFIND", body=b"")

        captured = {}

        def fake_app(environ, start_response):
            captured.update(environ)
            start_response("207 Multi-Status", [("Content-Type", "application/xml")])
            return _ClosableResult([b"<multistatus/>"])

        with (
            mock.patch(
                "odoo.addons.base_dav.controllers.main.radicale_config.load"
            ) as load_config,
            mock.patch(
                "odoo.addons.base_dav.controllers.main.Application",
                return_value=fake_app,
            ),
        ):
            load_config.return_value = mock.Mock()
            response = self.controller.handle_dav_request("demo/path")

        self.assertEqual(response.status_code, 207)
        self.assertEqual(captured["SCRIPT_NAME"], PREFIX)
        self.assertEqual(captured["HTTP_X_SCRIPT_NAME"], PREFIX)
        self.assertEqual(captured["PATH_INFO"], "/demo/path")
        self.assertEqual(captured["CONTENT_TYPE"], "application/xml; charset=utf-8")
        self.assertEqual(captured["REQUEST_METHOD"], "PROPFIND")
        body = captured["wsgi.input"].read()
        self.assertEqual(body, b"")
        self.assertEqual(captured["CONTENT_LENGTH"], "0")

    def test_handle_dav_request_preserves_request_body(self):
        self._push_request(method="PROPFIND", body=b"<propfind/>")

        captured = {}

        def fake_app(environ, start_response):
            captured.update(environ)
            start_response("207 Multi-Status", [("Content-Type", "application/xml")])
            return _ClosableResult([b"<multistatus/>"])

        with (
            mock.patch(
                "odoo.addons.base_dav.controllers.main.radicale_config.load"
            ) as load_config,
            mock.patch(
                "odoo.addons.base_dav.controllers.main.Application",
                return_value=fake_app,
            ),
        ):
            load_config.return_value = mock.Mock()
            response = self.controller.handle_dav_request("demo/path")

        self.assertEqual(response.status_code, 207)
        self.assertEqual(captured["wsgi.input"].read(), b"<propfind/>")
        self.assertEqual(captured["CONTENT_LENGTH"], str(len(b"<propfind/>")))

    def test_handle_dav_request_uses_given_body_and_default_root_path(self):
        body = b"<xml>payload</xml>"
        self._push_request(method="PUT", body=body, environ={"REQUEST_METHOD": "PUT"})

        captured = {}

        def fake_app(environ, start_response):
            captured.update(environ)
            start_response("201 Created", [("X-Test", "yes")])
            return _ClosableResult([b"created"])

        with (
            mock.patch(
                "odoo.addons.base_dav.controllers.main.radicale_config.load"
            ) as load_config,
            mock.patch(
                "odoo.addons.base_dav.controllers.main.Application",
                return_value=fake_app,
            ),
        ):
            load_config.return_value = mock.Mock()
            response = self.controller.handle_dav_request()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(captured["PATH_INFO"], "/")
        self.assertEqual(captured["CONTENT_LENGTH"], str(len(body)))
        self.assertEqual(captured["wsgi.input"].read(), body)
        self.assertEqual(response.headers.get("X-Test"), "yes")

    def test_handle_dav_request_accepts_dict_headers_and_closes_iterable(self):
        self._push_request(method="GET", body=b"hello")

        result_iter = _ClosableResult([b"done"])

        def fake_app(environ, start_response):
            start_response("200 OK", {"X-Mode": "dict"})
            return result_iter

        with (
            mock.patch(
                "odoo.addons.base_dav.controllers.main.radicale_config.load"
            ) as load_config,
            mock.patch(
                "odoo.addons.base_dav.controllers.main.Application",
                return_value=fake_app,
            ),
        ):
            load_config.return_value = mock.Mock()
            response = self.controller.handle_dav_request("x")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Mode"), "dict")
        self.assertTrue(result_iter.closed)
