# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from base64 import b64encode
from unittest import mock
from urllib.parse import urlparse

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from ..controllers.main import PREFIX
from ..controllers.main import Main as Controller

ADMIN_PASSWORD = "RadicalePa$$word"


@mute_logger("radicale")
class TestBaseDav(TransactionCase):
    def _patch_request(self, module):
        original = module.request
        request_mock = mock.Mock()
        module.request = request_mock
        self.addCleanup(setattr, module, "request", original)
        return request_mock

    def setUp(self):
        super().setUp()

        from ..controllers import main as controllers_main
        from ..radicale import auth as radicale_auth
        from ..radicale import collection as radicale_collection

        self.req_mock = self._patch_request(controllers_main)
        self.auth_mock = self._patch_request(radicale_auth)
        self.coll_mock = self._patch_request(radicale_collection)

        self.collection = self.env["dav.collection"].create({
            "name": "Test Collection",
            "dav_type": "calendar",
            "model_id": self.env.ref("base.model_res_users").id,
            "domain": "[]",
        })

        self.dav_path = urlparse(self.collection.url).path.replace(PREFIX, '')

        self.controller = Controller()
        self.env.user.password_crypt = ADMIN_PASSWORD

        self.test_user = self.env["res.users"].create({
            "login": "tester",
            "name": "tester",
        })

        self.auth_owner = self.auth_string(self.env.user, ADMIN_PASSWORD)
        self.auth_tester = self.auth_string(self.test_user, ADMIN_PASSWORD)

    def auth_string(self, user, password):
        return b64encode(
            ("%s:%s" % (user.login, password)).encode()
        ).decode()

    def init_mocks(self):
        self.req_mock.env = self.env
        self.req_mock.httprequest.environ = {
            "HTTP_AUTHORIZATION": "Basic %s" % self.auth_owner,
            "REQUEST_METHOD": "PROPFIND",
            "HTTP_X_SCRIPT_NAME": PREFIX,
        }

        self.auth_mock.env["res.users"]._login.return_value = self.env.uid
        self.auth_mock.env["res.users"].authenticate.return_value = self.env.uid
        self.coll_mock.env = self.env

    def check_status_code(self, response, forbidden):
        if forbidden:
            self.assertNotEqual(response.status_code, 403)
        else:
            self.assertEqual(response.status_code, 403)

    def check_access(self, environ, auth_string, read, write):
        environ.update({
            "REQUEST_METHOD": "PROPFIND",
            "HTTP_AUTHORIZATION": "Basic %s" % auth_string,
        })
        response = self.controller.handle_dav_request(self.dav_path)
        self.check_status_code(response, read)

        environ["REQUEST_METHOD"] = "PUT"
        response = self.controller.handle_dav_request(self.dav_path)
        self.check_status_code(response, write)

    def test_well_known(self):
        self.req_mock.env = self.env

        response = self.controller.handle_well_known_request()
        self.assertEqual(response.status_code, 301)

    def test_authenticated(self):
        self.init_mocks()
        environ = self.req_mock.httprequest.environ

        self.collection.rights = "authenticated"

        self.check_access(environ, self.auth_owner, read=True, write=True)
        self.check_access(environ, self.auth_tester, read=True, write=True)

    def test_owner_only(self):
        self.init_mocks()
        environ = self.req_mock.httprequest.environ

        self.collection.rights = "owner_only"

        self.check_access(environ, self.auth_owner, read=True, write=True)
        self.check_access(environ, self.auth_tester, read=False, write=False)

    def test_owner_write_only(self):
        self.init_mocks()
        environ = self.req_mock.httprequest.environ

        self.collection.rights = "owner_write_only"

        self.check_access(environ, self.auth_owner, read=True, write=True)
        self.check_access(environ, self.auth_tester, read=True, write=False)
