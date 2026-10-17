# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Regression tests for the DAV Bearer-token authentication path.

PR #3 added ``authenticate_with_bearer`` and switched the DAV upload routes
to validate API keys with the dedicated ``dav`` scope. These tests pin the
contract that work relies on:

* a key issued with ``scope="dav"`` validates for ``dav`` and is rejected
  for ``rpc`` (so a DAV token cannot be replayed against the RPC endpoint);
* a key issued with no scope (the default from Odoo's own API-key UI) keeps
  working for both scopes, so existing clients are unaffected;
* an unknown key validates for neither scope.
"""

from odoo.tests.common import TransactionCase


class TestDavBearerAuth(TransactionCase):
    def _make_user(self):
        return self.env["res.users"].create(
            {
                "name": "DAV Bearer Test User",
                "login": "dav_bearer_test_user",
                "email": "dav_bearer_test_user@example.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )

    def test_dav_scoped_key_validates_only_for_dav(self):
        user = self._make_user()
        key = self.env["res.users.apikeys"].with_user(user)._generate(
            "dav", "dav bearer test key"
        )
        apikeys = self.env["res.users.apikeys"]
        self.assertEqual(
            apikeys._check_credentials(scope="dav", key=key),
            user.id,
            "a dav-scoped key must validate for the dav scope",
        )
        self.assertFalse(
            apikeys._check_credentials(scope="rpc", key=key),
            "a dav-scoped key must NOT validate for the rpc scope",
        )

    def test_unscoped_key_validates_for_both_scopes(self):
        user = self._make_user()
        key = self.env["res.users.apikeys"].with_user(user)._generate(
            None, "unscoped test key"
        )
        apikeys = self.env["res.users.apikeys"]
        self.assertEqual(
            apikeys._check_credentials(scope="dav", key=key),
            user.id,
        )
        self.assertEqual(
            apikeys._check_credentials(scope="rpc", key=key),
            user.id,
        )

    def test_invalid_key_rejected_for_dav(self):
        apikeys = self.env["res.users.apikeys"]
        self.assertFalse(
            apikeys._check_credentials(scope="dav", key="not-a-real-key-xxxx"),
            "an unknown key must not validate",
        )
