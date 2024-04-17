# © 2024 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestAccountBankStatementImportPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.no_partner_write_group = cls.env["res.groups"].create(
            {
                "name": "Partner write restriction group",
            }
        )
        cls.env["ir.rule"].create(
            {
                "name": "Partner write restriction rule",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "domain_force": "[(0, '=', 1)]",
                "and_restriction_for_groups": True,
                "groups": [(Command.LINK, cls.no_partner_write_group.id)],
            }
        )
        cls.permission_user = cls.env["res.users"].create(
            {
                "name": "Limited permissions user",
                "login": "lpu",
                "password": "lpu_pass",
                "groups_id": [
                    (4, cls.env.ref("base.group_user").id),
                    (4, cls.env.ref("base.group_partner_manager").id),
                    (4, cls.no_partner_write_group.id),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})

    def test_partner_manipulation(self):
        self.assertFalse(self.partner.email)

        # Check restrictive permission is not letting modify res.partner
        with self.assertRaises(AccessError):
            self.partner.with_user(self.permission_user).write(
                {"email": "test@test.com"}
            )
        self.assertFalse(self.partner.email)

        # Remove restrictive permission
        self.permission_user.write(
            {"groups_id": [(Command.UNLINK, self.no_partner_write_group.id)]}
        )

        # Check record can now be modified
        self.partner.with_user(self.permission_user).write({"email": "test@test.com"})
        self.assertEqual(self.partner.email, "test@test.com")
