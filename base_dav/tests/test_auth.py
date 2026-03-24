# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace
from unittest import mock

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base_dav.radicale import auth as dav_auth_mod
from odoo.addons.base_dav.radicale.auth import Auth


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

    def _make_request(self, *, api_uid=None, exists=True, login=None):
        """Build a mocked request object for Auth._login_ext tests."""
        user_record = mock.Mock()
        user_record.exists.return_value = exists
        user_record.login = login or self.user.login

        apikeys_model = mock.Mock()
        apikeys_model._check_credentials.return_value = api_uid

        users_model = mock.Mock()
        users_model.sudo.return_value.browse.return_value = user_record

        env = mock.MagicMock()
        env.__getitem__.side_effect = lambda model_name: {
            "res.users.apikeys": apikeys_model,
            "res.users": users_model,
        }[model_name]
        env.user.login = login or self.user.login

        request_obj = SimpleNamespace(
            env=env,
            update_env=mock.Mock(),
        )
        return request_obj, apikeys_model, users_model, user_record

    def test_login_ext_returns_empty_without_login(self):
        auth = object.__new__(Auth)
        request_obj, apikeys_model, _, _ = self._make_request()

        with mock.patch.object(dav_auth_mod, "request", request_obj):
            result = auth._login_ext("", "secret", SimpleNamespace())

        self.assertEqual(result, "")
        apikeys_model._check_credentials.assert_not_called()
        request_obj.update_env.assert_not_called()

    def test_login_ext_returns_empty_without_password(self):
        auth = object.__new__(Auth)
        request_obj, apikeys_model, _, _ = self._make_request()

        with mock.patch.object(dav_auth_mod, "request", request_obj):
            result = auth._login_ext(self.user.login, "", SimpleNamespace())

        self.assertEqual(result, "")
        apikeys_model._check_credentials.assert_not_called()
        request_obj.update_env.assert_not_called()

    def test_login_ext_returns_empty_when_key_is_invalid(self):
        auth = object.__new__(Auth)
        request_obj, apikeys_model, _, _ = self._make_request(api_uid=False)

        with (
            mock.patch.object(dav_auth_mod, "request", request_obj),
            mock.patch.object(dav_auth_mod, "_logger") as logger,
        ):
            result = auth._login_ext(self.user.login, "bad-key", SimpleNamespace())

        self.assertEqual(result, "")
        apikeys_model._check_credentials.assert_called_once_with(
            scope="dav",
            key="bad-key",
        )
        request_obj.update_env.assert_not_called()
        logger.info.assert_called_once()

    def test_login_ext_returns_empty_when_user_not_found(self):
        auth = object.__new__(Auth)
        request_obj, apikeys_model, users_model, _ = self._make_request(
            api_uid=self.user.id,
            exists=False,
        )

        with (
            mock.patch.object(dav_auth_mod, "request", request_obj),
            mock.patch.object(dav_auth_mod, "_logger") as logger,
        ):
            result = auth._login_ext(self.user.login, "secret", SimpleNamespace())

        self.assertEqual(result, "")
        apikeys_model._check_credentials.assert_called_once_with(
            scope="dav",
            key="secret",
        )
        users_model.sudo.return_value.browse.assert_called_once_with(self.user.id)
        request_obj.update_env.assert_not_called()
        logger.info.assert_called_once()

    def test_login_ext_returns_empty_when_login_does_not_match_user(self):
        auth = object.__new__(Auth)
        request_obj, apikeys_model, users_model, _ = self._make_request(
            api_uid=self.user.id,
            login="another_login",
        )

        with (
            mock.patch.object(dav_auth_mod, "request", request_obj),
            mock.patch.object(dav_auth_mod, "_logger") as logger,
        ):
            result = auth._login_ext(self.user.login, "secret", SimpleNamespace())

        self.assertEqual(result, "")
        apikeys_model._check_credentials.assert_called_once_with(
            scope="dav",
            key="secret",
        )
        users_model.sudo.return_value.browse.assert_called_once_with(self.user.id)
        request_obj.update_env.assert_not_called()
        logger.info.assert_called_once()

    def test_login_ext_accepts_valid_api_key(self):
        auth = object.__new__(Auth)
        request_obj, apikeys_model, users_model, _ = self._make_request(
            api_uid=self.user.id,
            login=self.user.login,
        )

        with mock.patch.object(dav_auth_mod, "request", request_obj):
            result = auth._login_ext(
                self.user.login,
                "secret",
                SimpleNamespace(),
            )

        self.assertEqual(result, self.user.login)
        apikeys_model._check_credentials.assert_called_once_with(
            scope="dav",
            key="secret",
        )
        users_model.sudo.return_value.browse.assert_called_once_with(self.user.id)
        request_obj.update_env.assert_called_once_with(user=self.user.id)
