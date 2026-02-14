# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace
from unittest import mock

from odoo import http
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base_dav.radicale.auth import Auth, _set_request_user, _user_agent_env


@tagged("post_install", "-at_install")
class TestDavAuth(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "DAV Tester",
                    "login": "dav_tester",
                    "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
                }
            )
        )

    def setUp(self):
        super().setUp()
        self.request_obj = SimpleNamespace(
            env=self.env,
            uid=self.env.uid,
            update_env=mock.Mock(),
        )
        http._request_stack.push(self.request_obj)
        self.addCleanup(http._request_stack.pop)

    def test_user_agent_env_minimal(self):
        self.assertEqual(_user_agent_env(SimpleNamespace()), {"interactive": False})

    def test_user_agent_env_full(self):
        ctx = SimpleNamespace(
            user_agent="Thunderbird",
            remote_host="10.0.0.5",
        )
        self.assertEqual(
            _user_agent_env(ctx),
            {
                "interactive": False,
                "HTTP_USER_AGENT": "Thunderbird",
                "REMOTE_ADDR": "10.0.0.5",
            },
        )

    def test_user_agent_env_remote_from_tuple_client(self):
        ctx = SimpleNamespace(
            user_agent=None,
            remote_host=None,
            remote_addr=None,
            client=("10.10.10.10", 1234),
        )
        self.assertEqual(
            _user_agent_env(ctx),
            {
                "interactive": False,
                "REMOTE_ADDR": "10.10.10.10",
            },
        )

    def test_set_request_user(self):
        _set_request_user(self.env, self.user.id)
        self.request_obj.update_env.assert_called_once_with(user=self.user.id)

    def test_login_ext_returns_empty_on_login_exception(self):
        auth = object.__new__(Auth)
        with (
            mock.patch.object(
                type(self.env["res.users"]),
                "_login",
                side_effect=Exception("boom"),
            ),
            mock.patch("odoo.addons.base_dav.radicale.auth._logger") as logger,
        ):
            result = auth._login_ext("bad", "bad", SimpleNamespace())

        self.assertEqual(result, "")
        logger.info.assert_called_once()

    def test_login_ext_returns_empty_on_missing_uid(self):
        auth = object.__new__(Auth)
        with mock.patch.object(
            type(self.env["res.users"]),
            "_login",
            return_value={},
        ):
            result = auth._login_ext("bad", "bad", SimpleNamespace())
        self.assertEqual(result, "")

    def test_login_ext_accepts_dict_response(self):
        auth = object.__new__(Auth)
        with (
            mock.patch.object(
                type(self.env["res.users"]),
                "_login",
                return_value={"uid": self.user.id},
            ),
            mock.patch(
                "odoo.addons.base_dav.radicale.auth._set_request_user"
            ) as set_request_user,
        ):
            result = auth._login_ext(
                self.user.login,
                "secret",
                SimpleNamespace(user_agent="TB", remote_addr="127.0.0.1"),
            )

        self.assertEqual(result, self.user.login)
        set_request_user.assert_called_once_with(self.env, self.user.id)

    def test_login_ext_accepts_int_response(self):
        auth = object.__new__(Auth)
        with (
            mock.patch.object(
                type(self.env["res.users"]),
                "_login",
                return_value=self.user.id,
            ),
            mock.patch(
                "odoo.addons.base_dav.radicale.auth._set_request_user"
            ) as set_request_user,
        ):
            result = auth._login_ext(
                self.user.login,
                "secret",
                SimpleNamespace(),
            )

        self.assertEqual(result, self.user.login)
        set_request_user.assert_called_once_with(self.env, self.user.id)
