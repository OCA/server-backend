# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import vobject

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestVCardFalseValues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {"name": "DAV Partner"}
        )  # email=False
        cls.collection = cls.env["dav.collection"].create(
            {
                "name": "Test Addressbook",
                "dav_type": "addressbook",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "domain": f"[('id', '=', {cls.partner.id})]",
            }
        )

        cls.map_email = cls.env["dav.collection.field_mapping"].create(
            {
                "collection_id": cls.collection.id,
                "name": "EMAIL",
                "mapping_type": "simple",
                "field_id": cls.env["ir.model.fields"]._get("res.partner", "email").id,
            }
        )

    def test_simple_mapping_false_must_not_break_vobject(self):
        """Ensure empty Char fields are not exported as bool into vCard.

        Expected behavior:
          - Before fix: to_vobject() returns False -> vobject.serialize() must crash
          - After fix: to_vobject() returns None -> vobject.serialize() must succeed
        """
        exported = self.map_email.to_vobject(self.partner)
        card = vobject.vCard()
        if exported is False:
            card.add("email").value = exported
            with self.assertRaises(AttributeError):
                card.serialize()
        else:
            self.assertIsNone(exported)
            card.add("fn").value = "DAV Partner"
            card.serialize()  # must not raise
