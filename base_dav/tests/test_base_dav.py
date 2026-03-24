# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from types import SimpleNamespace

import odoo.http as http
from odoo.tests.common import TransactionCase, tagged

from ..controllers.main import PREFIX
from ..controllers.main import Main as Controller
from ..radicale.rights import Rights


@tagged("post_install", "-at_install")
class TestBaseDav(TransactionCase):
    @classmethod
    def setUpClass(cls):
        """Prepare test users, DAV collection and controller for rights tests."""
        super().setUpClass()

        # Ensure we have a normal internal user for non-owner checks
        group_user = cls.env.ref("base.group_user")
        cls.test_user = cls.env["res.users"].create(
            {
                "login": "tester",
                "name": "tester",
                "groups_id": [(6, 0, [group_user.id])],
            }
        )

        # Create a minimal dav.collection
        # Use res.partner (safe to create/delete in tests)
        cls.partner = cls.env["res.partner"].create({"name": "DAV Partner"})
        cls.collection = cls.env["dav.collection"].create(
            {
                "name": "Test Collection",
                "dav_type": "calendar",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "domain": f"[('id', '=', {cls.partner.id})]",
            }
        )

        # NOTE: In our rights logic, owner is path's first segment (login)
        cls.owner_login = cls.env.user.login
        cls.tester_login = cls.test_user.login

        cls.controller = Controller()

    def setUp(self):
        """Bind HTTP request context and initialize Rights instance."""
        super().setUp()

        # Bind odoo.http.request LocalProxy (needed because Rights uses request.env)
        req = SimpleNamespace(env=self.env, uid=self.env.uid)
        http._request_stack.push(req)
        self.addCleanup(http._request_stack.pop)

        # Instantiate Rights without calling BaseRights.__init__
        self.rights = object.__new__(Rights)

    def _assert_perm(self, user_login, path, expect_r, expect_w):
        """Assert expected read/write permissions for given user and path."""
        perms = self.rights.authorization(user_login, path) or ""
        self.assertEqual(
            "r" in perms,
            expect_r,
            f"permissions={perms!r} user={user_login!r} path={path!r}",
        )
        self.assertEqual(
            "w" in perms,
            expect_w,
            f"permissions={perms!r} user={user_login!r} path={path!r}",
        )

    def test_well_known(self):
        """Verify that well-known DAV endpoints redirect to the DAV prefix."""
        resp = self.controller.handle_well_known_request()
        self.assertEqual(resp.status_code, 301)
        # redirect target must be /.dav
        self.assertIn(PREFIX, resp.location)

    def test_authenticated(self):
        """Verify access control for collections with 'authenticated' rights mode."""
        self.collection.rights = "authenticated"

        base = f"/{self.owner_login}/{self.collection.id}"
        item = f"{base}/{self.partner.id}"

        # owner: rw
        self._assert_perm(self.owner_login, base, True, True)
        self._assert_perm(self.owner_login, item, True, True)

        # other authenticated user: rw
        self._assert_perm(self.tester_login, base, True, True)
        self._assert_perm(self.tester_login, item, True, True)

        # anonymous: none
        self._assert_perm("", base, False, False)
        self._assert_perm("", item, False, False)

    def test_owner_only(self):
        """Verify access control for collections with 'owner_only' rights mode."""
        self.collection.rights = "owner_only"

        base = f"/{self.owner_login}/{self.collection.id}"
        item = f"{base}/{self.partner.id}"

        # owner: rw
        self._assert_perm(self.owner_login, base, True, True)
        self._assert_perm(self.owner_login, item, True, True)

        # other authenticated user: none
        self._assert_perm(self.tester_login, base, False, False)
        self._assert_perm(self.tester_login, item, False, False)

        # anonymous: none
        self._assert_perm("", base, False, False)
        self._assert_perm("", item, False, False)

    def test_owner_write_only(self):
        """Verify access control for collections with 'owner_write_only' rights mode."""
        self.collection.rights = "owner_write_only"

        base = f"/{self.owner_login}/{self.collection.id}"
        item = f"{base}/{self.partner.id}"

        # owner: rw
        self._assert_perm(self.owner_login, base, True, True)
        self._assert_perm(self.owner_login, item, True, True)

        # other authenticated user: r only
        self._assert_perm(self.tester_login, base, True, False)
        self._assert_perm(self.tester_login, item, True, False)

        # anonymous: none
        self._assert_perm("", base, False, False)
        self._assert_perm("", item, False, False)

    def test_rights_root_and_principal_and_missing_collection(self):
        """Verify root/principal paths and missing collection handling."""
        self._assert_perm(self.owner_login, "/", True, True)
        self._assert_perm("", "/", False, False)

        self._assert_perm(self.owner_login, f"/{self.owner_login}", True, True)
        self._assert_perm("", f"/{self.owner_login}", False, False)

        self._assert_perm(self.owner_login, f"/{self.owner_login}/999999", False, False)
        self._assert_perm(
            self.owner_login, f"/{self.owner_login}/not-a-number", False, False
        )
