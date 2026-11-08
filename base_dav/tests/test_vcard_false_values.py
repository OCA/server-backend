# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import vobject

from odoo.tests import tagged

from .common import BaseDavTestCase


@tagged("post_install", "-at_install")
class TestVCardFalseValues(BaseDavTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.create_partner(
            name="DAV Partner",
            email=False,
        )
        fixture = cls.create_partner_addressbook_fixture(
            partner=cls.partner,
            name="Test Addressbook",
            with_name=False,
            with_email=False,
        )
        cls.collection = fixture.collection
        cls.map_email = cls.add_mapping(
            cls.collection,
            name="EMAIL",
            field_xmlid="base.field_res_partner__email",
        )

    def test_simple_mapping_false_must_not_break_vobject(self):
        """Verify falsey Char export returns None and does not break vobject."""
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
