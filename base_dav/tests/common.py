# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
from contextlib import contextmanager
from types import SimpleNamespace
from urllib.parse import quote_plus

import odoo.http as http
from odoo.tests.common import TransactionCase

from ..radicale.collection import Collection


class BaseDavTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    @classmethod
    def create_user(cls, login, *, name=None, groups=None):
        groups = groups or ["base.group_user"]
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": login,
                    "name": name or login,
                    "groups_id": [(6, 0, [cls.env.ref(xmlid).id for xmlid in groups])],
                }
            )
        )

    @classmethod
    def create_partner(cls, *, name, email=False, **extra_vals):
        vals = {
            "name": name,
            "email": email,
            **extra_vals,
        }
        return cls.env["res.partner"].create(vals)

    @classmethod
    def create_collection(
        cls,
        *,
        name,
        dav_type,
        model_xmlid,
        domain="[]",
        rights="owner_only",
        field_uuid_xmlid=None,
    ):
        vals = {
            "name": name,
            "dav_type": dav_type,
            "model_id": cls.env.ref(model_xmlid).id,
            "domain": domain,
            "rights": rights,
        }
        if field_uuid_xmlid:
            vals["field_uuid"] = cls.env.ref(field_uuid_xmlid).id
        return cls.env["dav.collection"].create(vals)

    @classmethod
    def add_mapping(
        cls,
        collection,
        *,
        name,
        field_xmlid,
        import_code=None,
        export_code=None,
    ):
        return cls.env["dav.collection.field_mapping"].create(
            {
                "collection_id": collection.id,
                "name": name,
                "field_id": cls.env.ref(field_xmlid).id,
                "mapping_type": "code" if (import_code or export_code) else "simple",
                "import_code": import_code,
                "export_code": export_code,
            }
        )

    @classmethod
    def create_attachment(
        cls,
        *,
        record,
        name,
        raw=b"",
        mimetype="application/octet-stream",
    ):
        return cls.env["ir.attachment"].create(
            {
                "name": name,
                "type": "binary",
                "datas": base64.b64encode(raw).decode(),
                "res_model": record._name,
                "res_id": record.id,
                "mimetype": mimetype,
            }
        )

    @classmethod
    def create_partner_addressbook_fixture(
        cls,
        *,
        partner=None,
        name="Contacts",
        rights="owner_only",
        domain=None,
        with_name=True,
        with_email=True,
    ):
        partner = partner or cls.create_partner(
            name="DAV Partner",
            email="dav@example.com",
        )
        domain = domain or f"[('id', '=', {partner.id})]"
        collection = cls.create_collection(
            name=name,
            dav_type="addressbook",
            model_xmlid="base.model_res_partner",
            domain=domain,
            rights=rights,
        )

        mappings = {}
        if with_name:
            mappings["name"] = cls.add_mapping(
                collection,
                name="FN",
                field_xmlid="base.field_res_partner__name",
            )
        if with_email:
            mappings["email"] = cls.add_mapping(
                collection,
                name="EMAIL",
                field_xmlid="base.field_res_partner__email",
            )

        return SimpleNamespace(
            partner=partner,
            collection=collection,
            mappings=mappings,
        )

    @classmethod
    def create_users_calendar_fixture(
        cls,
        *,
        record=None,
        name="Test Collection",
        rights="owner_only",
        domain="[]",
    ):
        collection = cls.create_collection(
            name=name,
            dav_type="calendar",
            model_xmlid="base.model_res_users",
            domain=domain,
            rights=rights,
        )
        login_mapping = cls.add_mapping(
            collection,
            name="login",
            field_xmlid="base.field_res_users__login",
            import_code="result = item.value",
            export_code="result = record.login",
        )
        name_mapping = cls.add_mapping(
            collection,
            name="name",
            field_xmlid="base.field_res_users__name",
        )
        record = record or cls.create_user("tester", name="Test User")

        return SimpleNamespace(
            record=record,
            collection=collection,
            mappings={
                "login": login_mapping,
                "name": name_mapping,
            },
        )

    @classmethod
    def create_files_fixture(
        cls,
        *,
        partner=None,
        collection_name="Partner Files",
        attachment_name="hello world.txt",
        attachment_raw=b"Hello DAV files",
        mimetype="text/plain",
    ):
        partner = partner or cls.create_partner(
            name="DAV Files Partner",
            email="files@example.com",
        )
        collection = cls.create_collection(
            name=collection_name,
            dav_type="files",
            model_xmlid="base.model_res_partner",
            domain=f"[('id', '=', {partner.id})]",
        )
        attachment = cls.create_attachment(
            record=partner,
            name=attachment_name,
            raw=attachment_raw,
            mimetype=mimetype,
        )
        return SimpleNamespace(
            partner=partner,
            collection=collection,
            attachment=attachment,
        )

    @contextmanager
    def request_context(self, *, env=None, uid=None):
        request_obj = SimpleNamespace(
            env=env or self.env,
            uid=uid or self.env.uid,
        )
        http._request_stack.push(request_obj)
        try:
            yield request_obj
        finally:
            http._request_stack.pop()

    def push_request_context(self, *, env=None, uid=None):
        ctx = self.request_context(env=env, uid=uid)
        ctx.__enter__()
        self.addCleanup(ctx.__exit__, None, None, None)

    def make_collection(self, collection, *, login=None):
        login = login or self.env.user.login
        return Collection(f"{login}/{collection.id}")

    @staticmethod
    def dav_quote(value):
        return quote_plus(value or "")

    def assert_permissions(self, rights_obj, user_login, path, *, can_read, can_write):
        perms = rights_obj.authorization(user_login, path) or ""
        self.assertEqual(
            "r" in perms,
            can_read,
            f"permissions={perms!r} user={user_login!r} path={path!r}",
        )
        self.assertEqual(
            "w" in perms,
            can_write,
            f"permissions={perms!r} user={user_login!r} path={path!r}",
        )
