# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace
from unittest import mock

from odoo import http
from odoo.tests import tagged

from odoo.addons.base_dav.controllers.main import PREFIX, Main

from .common import BaseDavTestCase


class _ClosableResult(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False

    def close(self):
        self.closed = True


@tagged("post_install", "-at_install")
class TestDavController(BaseDavTestCase):
    def setUp(self):
        super().setUp()
        self.controller = Main()

    def _push_request(
        self,
        *,
        method="PROPFIND",
        body=b"",
        environ=None,
        content_type="application/xml; charset=utf-8",
    ):
        default_environ = {
            "REQUEST_METHOD": method,
            "CONTENT_LENGTH": str(len(body)),
            "CONTENT_TYPE": content_type,
        }
        if environ:
            default_environ.update(environ)

        httprequest = SimpleNamespace(
            environ=default_environ,
            method=method,
            get_data=lambda cache=False: body,
        )
        request_obj = SimpleNamespace(
            httprequest=httprequest,
            env=self.env,
            uid=self.env.uid,
        )
        http._request_stack.push(request_obj)
        self.addCleanup(http._request_stack.pop)
        return request_obj

    @staticmethod
    def _make_fake_app(captured, *, status, headers, payload):
        def fake_app(environ, start_response):
            captured.update(environ)
            start_response(status, headers)
            return _ClosableResult([payload])

        return fake_app

    def test_handle_dav_request_preserves_empty_propfind_body(self):
        self._push_request(method="PROPFIND", body=b"")

        captured = {}
        fake_app = self._make_fake_app(
            captured,
            status="207 Multi-Status",
            headers=[("Content-Type", "application/xml")],
            payload=b"<multistatus/>",
        )

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
        self.assertEqual(captured["wsgi.input"].read(), b"")
        self.assertEqual(captured["CONTENT_LENGTH"], "0")

    def test_handle_dav_request_preserves_request_body(self):
        body = b"<propfind/>"
        self._push_request(method="PROPFIND", body=body)

        captured = {}
        fake_app = self._make_fake_app(
            captured,
            status="207 Multi-Status",
            headers=[("Content-Type", "application/xml")],
            payload=b"<multistatus/>",
        )

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
        self.assertEqual(captured["wsgi.input"].read(), body)
        self.assertEqual(captured["CONTENT_LENGTH"], str(len(body)))

    def test_handle_dav_request_uses_given_body_and_default_root_path(self):
        body = b"<xml>payload</xml>"
        self._push_request(
            method="PUT",
            body=body,
            environ={"REQUEST_METHOD": "PUT"},
        )

        captured = {}
        fake_app = self._make_fake_app(
            captured,
            status="201 Created",
            headers=[("X-Test", "yes")],
            payload=b"created",
        )

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
