# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestModelAccessRestriction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env.ref("base.model_res_partner")
        cls.model2 = cls.env.ref("base.model_res_partner_category")
        cls.group = cls.env["res.groups"].create(
            {
                "name": "Test Group",
            }
        )
        cls.restriction = cls.env["ir.model.access.restriction"].create(
            {
                "name": "Test Restriction",
                "model_id": cls.model.id,
                "perm_create": True,
                "perm_unlink": True,
                "perm_write": True,
                "perm_read": True,
                "groups": [(4, cls.group.id)],
            }
        )
        cls.restriction2 = cls.env["ir.model.access.restriction"].create(
            {
                "name": "Test Restriction",
                "model_id": cls.model2.id,
                "perm_create": False,
                "perm_unlink": False,
                "perm_write": False,
                "perm_read": False,
                "groups": [(4, cls.group.id)],
            }
        )

    def test_restriction(self):
        self.assertFalse(self.env["res.partner"].check_access_rights("create", False))
        self.assertFalse(self.env["res.partner"].check_access_rights("unlink", False))
        self.assertFalse(self.env["res.partner"].check_access_rights("write", False))
        self.assertFalse(self.env["res.partner"].check_access_rights("read", False))
        self.assertTrue(
            self.env["res.partner.category"].check_access_rights("create", False)
        )
        self.assertTrue(
            self.env["res.partner.category"].check_access_rights("unlink", False)
        )
        self.assertTrue(
            self.env["res.partner.category"].check_access_rights("write", False)
        )
        self.assertTrue(
            self.env["res.partner.category"].check_access_rights("read", False)
        )

    def test_restriction_passed(self):
        self.group.write({"users": [(4, self.env.uid)]})
        self.assertTrue(self.env["res.partner"].check_access_rights("create", False))
        self.assertTrue(self.env["res.partner"].check_access_rights("unlink", False))
        self.assertTrue(self.env["res.partner"].check_access_rights("write", False))
        self.assertTrue(self.env["res.partner"].check_access_rights("read", False))

    def test_no_restriction(self):
        self.restriction.unlink()
        self.assertTrue(self.env["res.partner"].check_access_rights("create", False))

    def test_two_restrictions(self):
        self.restriction2 = self.env["ir.model.access.restriction"].create(
            {
                "name": "Test Restriction 2",
                "model_id": self.model.id,
                "perm_create": True,
                "perm_unlink": True,
                "groups": [(4, self.env.ref("base.group_user").id)],
            }
        )
        self.assertFalse(self.env["res.partner"].check_access_rights("create", False))

    def test_access_exception(self):
        with self.assertRaises(AccessError):
            self.env["res.partner"].check_access_rights("create")

    def test_resctiction_creation_exception(self):
        with self.assertRaises(ValidationError):
            self.restriction = self.env["ir.model.access.restriction"].create(
                {
                    "name": "Test Restriction",
                    "model_id": self.model.id,
                    "groups": False,
                }
            )
