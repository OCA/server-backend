# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from lxml import etree

from odoo.tests.common import TransactionCase

from odoo.addons.base.models.res_users import name_boolean_group


class TestBasePortalGroup(TransactionCase):
    def test_portal_group_view(self):
        """Test that a group is added to the users form twice"""
        group = self.env["res.groups"].create(
            {
                "name": "Test Group",
                "category_id": self.env.ref("base_portal_type.category_portal_type").id,
            }
        )
        group_field_name = name_boolean_group(group.id)
        groups_view = etree.fromstring(self.env.ref("base.user_groups_view").arch)
        self.assertEqual(
            len(groups_view.xpath("//field[@name='%s']" % group_field_name)), 3
        )


class TestNoOtherSectionOnView(TransactionCase):
    def test_portal_group_view_no_other_section(self):
        """
        Test that if no portal groups exists without a category_id set,
        no 'Other' section is created.
        """
        self.env["res.groups"].search(
            [
                ("portal", "=", True),
                ("category_id", "=", False),
            ]
        ).unlink()
        # adding a portal group to guarantee the view extension
        self.env["res.groups"].create(
            {
                "name": "Test Group",
                "portal": True,
                "category_id": self.env.ref("base_portal_type.category_portal_type").id,
            }
        )

        groups_view = etree.fromstring(self.env.ref("base.user_groups_view").arch)
        group_elem = groups_view.xpath("//group[@name='base_portal_type_extension']")

        # making sure the parent group element actually exists
        self.assertEqual(len(group_elem), 1)
        # searching for the 'Other' section, which should not exist after unlinking above
        self.assertEqual(len(group_elem[0].xpath("//group[@string='Other']")), 0)
