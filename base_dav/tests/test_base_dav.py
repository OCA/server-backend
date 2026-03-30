# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from ..controllers.main import PREFIX
from ..controllers.main import Main as Controller
from ..radicale.rights import Rights
from .common import BaseDavTestCase


@tagged("post_install", "-at_install")
class TestBaseDav(BaseDavTestCase):
    @classmethod
    def setUpClass(cls):
        """Prepare shared users, partner, collection and controller."""
        super().setUpClass()

        cls.test_user = cls.create_user("tester", name="tester")
        cls.partner = cls.create_partner(name="DAV Partner")
        cls.collection = cls.create_collection(
            name="Test Collection",
            dav_type="calendar",
            model_xmlid="base.model_res_partner",
            domain=f"[('id', '=', {cls.partner.id})]",
        )

        cls.owner_login = cls.env.user.login
        cls.tester_login = cls.test_user.login

        cls.controller = Controller()

    def setUp(self):
        """Bind request context required by Rights.authorization()."""
        super().setUp()
        self.push_request_context()
        self.rights = object.__new__(Rights)

    def _collection_paths(self):
        """Return base collection path and item path for assertions."""
        base_path = f"/{self.owner_login}/{self.collection.id}"
        item_path = f"{base_path}/{self.partner.id}"
        return base_path, item_path

    def test_well_known(self):
        """Verify well-known DAV endpoint redirects to the DAV prefix."""
        response = self.controller.handle_well_known_request()

        self.assertEqual(response.status_code, 301)
        self.assertIn(PREFIX, response.location)

    def test_authenticated(self):
        """Verify authenticated rights grant rw to logged users only."""
        self.collection.rights = "authenticated"
        base_path, item_path = self._collection_paths()

        self.assert_permissions(
            self.rights,
            self.owner_login,
            base_path,
            can_read=True,
            can_write=True,
        )
        self.assert_permissions(
            self.rights,
            self.owner_login,
            item_path,
            can_read=True,
            can_write=True,
        )

        self.assert_permissions(
            self.rights,
            self.tester_login,
            base_path,
            can_read=True,
            can_write=True,
        )
        self.assert_permissions(
            self.rights,
            self.tester_login,
            item_path,
            can_read=True,
            can_write=True,
        )

        self.assert_permissions(
            self.rights,
            "",
            base_path,
            can_read=False,
            can_write=False,
        )
        self.assert_permissions(
            self.rights,
            "",
            item_path,
            can_read=False,
            can_write=False,
        )

    def test_owner_only(self):
        """Verify owner_only rights grant access only to the owner."""
        self.collection.rights = "owner_only"
        base_path, item_path = self._collection_paths()

        self.assert_permissions(
            self.rights,
            self.owner_login,
            base_path,
            can_read=True,
            can_write=True,
        )
        self.assert_permissions(
            self.rights,
            self.owner_login,
            item_path,
            can_read=True,
            can_write=True,
        )

        self.assert_permissions(
            self.rights,
            self.tester_login,
            base_path,
            can_read=False,
            can_write=False,
        )
        self.assert_permissions(
            self.rights,
            self.tester_login,
            item_path,
            can_read=False,
            can_write=False,
        )

        self.assert_permissions(
            self.rights,
            "",
            base_path,
            can_read=False,
            can_write=False,
        )
        self.assert_permissions(
            self.rights,
            "",
            item_path,
            can_read=False,
            can_write=False,
        )

    def test_owner_write_only(self):
        """Verify owner_write_only grants read-only access to other users."""
        self.collection.rights = "owner_write_only"
        base_path, item_path = self._collection_paths()

        self.assert_permissions(
            self.rights,
            self.owner_login,
            base_path,
            can_read=True,
            can_write=True,
        )
        self.assert_permissions(
            self.rights,
            self.owner_login,
            item_path,
            can_read=True,
            can_write=True,
        )

        self.assert_permissions(
            self.rights,
            self.tester_login,
            base_path,
            can_read=True,
            can_write=False,
        )
        self.assert_permissions(
            self.rights,
            self.tester_login,
            item_path,
            can_read=True,
            can_write=False,
        )

        self.assert_permissions(
            self.rights,
            "",
            base_path,
            can_read=False,
            can_write=False,
        )
        self.assert_permissions(
            self.rights,
            "",
            item_path,
            can_read=False,
            can_write=False,
        )

    def test_rights_root_and_principal_and_missing_collection(self):
        """Verify root, principal and invalid collection path handling."""
        self.assert_permissions(
            self.rights,
            self.owner_login,
            "/",
            can_read=True,
            can_write=True,
        )
        self.assert_permissions(
            self.rights,
            "",
            "/",
            can_read=False,
            can_write=False,
        )

        principal_path = f"/{self.owner_login}"
        self.assert_permissions(
            self.rights,
            self.owner_login,
            principal_path,
            can_read=True,
            can_write=True,
        )
        self.assert_permissions(
            self.rights,
            "",
            principal_path,
            can_read=False,
            can_write=False,
        )

        self.assert_permissions(
            self.rights,
            self.owner_login,
            f"/{self.owner_login}/999999",
            can_read=False,
            can_write=False,
        )
        self.assert_permissions(
            self.rights,
            self.owner_login,
            f"/{self.owner_login}/not-a-number",
            can_read=False,
            can_write=False,
        )
