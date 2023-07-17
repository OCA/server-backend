# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from lxml import etree

from odoo.tests.common import TransactionCase

from odoo.addons.base.models.res_users import name_boolean_group


class TestBasePortalGroup(TransactionCase):
    def test_portal_group_view(self):
        """Test that our group is added to the users form twice"""
        group = self.env.ref("base_portal_type.group_portal_type").copy()
        group_field_name = name_boolean_group(group.id)
        groups_view = etree.fromstring(self.env.ref("base.user_groups_view").arch)
        self.assertEqual(
            len(groups_view.xpath("//field[@name='%s']" % group_field_name)), 3
        )
