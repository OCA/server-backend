# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestUserProfile(TransactionCase):
    def _helper_unpack_groups_role(self, role):
        role_group_ids = role.trans_implied_ids.ids
        role_group_ids.append(role.group_id.id)
        return sorted(set(role_group_ids))

    def _helper_unpack_groups_group(self, group):
        group_ids = group.trans_implied_ids.ids
        group_ids.append(group.id)
        return sorted(set(group_ids))

    def setUp(self):
        super().setUp()
        self.user_model = self.env["res.users"]
        self.role_model = self.env["res.users.role"]

        self.company1 = self.env.ref("base.main_company")
        self.company2 = self.env["res.company"].create({"name": "company2"})

        self.default_user = self.env.ref("base.default_user")
        user_vals = {
            "name": "USER TEST (ROLES)",
            "login": "user_test_roles",
            "company_ids": [(6, 0, [self.company1.id, self.company2.id])],
            "company_id": self.company1.id,
        }
        self.user_id = self.user_model.create(user_vals)

        self.profile1_id = self.env["res.users.profile"].create(
            {"name": "profile1"}
        )
        self.profile2_id = self.env["res.users.profile"].create(
            {"name": "profile2"}
        )

        # role 1
        self.group_user_id = self.env.ref("base.group_user")
        self.group_no_one_id = self.env.ref("base.group_no_one")

        # role 2
        self.group_system_id = self.env.ref("base.group_system")
        self.group_multi_company_id = self.env.ref("base.group_multi_company")

        # role 3
        self.group_erp_manager_id = self.env.ref("base.group_erp_manager")
        self.group_partner_manager_id = self.env.ref(
            "base.group_partner_manager"
        )

        # roles 1 and 2 have a profile, role 3 no profile
        vals = {
            "name": "ROLE_1",
            "implied_ids": [
                (6, 0, [self.group_user_id.id, self.group_no_one_id.id])
            ],
            "profile_id": self.profile1_id.id,
        }
        self.role1_id = self.role_model.create(vals)
        self.role1_group_ids = self._helper_unpack_groups_role(self.role1_id)

        vals = {
            "name": "ROLE_2",
            "implied_ids": [
                (
                    6,
                    0,
                    [self.group_system_id.id, self.group_multi_company_id.id],
                )
            ],
            "profile_id": self.profile2_id.id,
        }
        self.role2_id = self.role_model.create(vals)
        self.role2_group_ids = self._helper_unpack_groups_role(self.role2_id)

        vals = {
            "name": "ROLE_3",
            "implied_ids": [
                (
                    6,
                    0,
                    [
                        self.group_erp_manager_id.id,
                        self.group_partner_manager_id.id,
                    ],
                )
            ],
        }
        self.role3_id = self.role_model.create(vals)
        self.role3_group_ids = self._helper_unpack_groups_role(self.role3_id)

    def test_filter_by_profile(self):
        line1_vals = {"role_id": self.role1_id.id, "user_id": self.user_id.id}
        self.user_id.write({"role_line_ids": [(0, 0, line1_vals)]})
        line2_vals = {"role_id": self.role2_id.id, "user_id": self.user_id.id}
        self.user_id.write({"role_line_ids": [(0, 0, line2_vals)]})
        self.assertEqual(
            self.user_id.profile_ids, self.profile1_id + self.profile2_id
        )
        self.assertEqual(self.user_id.profile_id, self.profile1_id)
        self.user_id.action_profile_change({"profile_id": self.profile1_id.id})

        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        expected_group_ids = sorted(set(self.role1_group_ids))
        self.assertEqual(user_group_ids, expected_group_ids)

        self.user_id.action_profile_change({"profile_id": self.profile2_id.id})

        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        expected_group_ids = sorted(set(self.role2_group_ids))
        self.assertEqual(user_group_ids, expected_group_ids)

    def test_allow_by_noprofile(self):
        line1_vals = {"role_id": self.role1_id.id, "user_id": self.user_id.id}
        self.user_id.write({"role_line_ids": [(0, 0, line1_vals)]})
        line2_vals = {"role_id": self.role3_id.id, "user_id": self.user_id.id}
        self.user_id.write({"role_line_ids": [(0, 0, line2_vals)]})
        self.assertEqual(self.user_id.profile_ids, self.profile1_id)
        user_group_ids = []
        for group in self.user_id.groups_id:
            user_group_ids += self._helper_unpack_groups_group(group)
        user_group_ids = set(user_group_ids)
        expected_groups = set(self.role1_group_ids + self.role3_group_ids)
        self.assertEqual(user_group_ids, expected_groups)

    def test_sync_profile_change_company(self):
        line1_vals = {
            "role_id": self.role1_id.id,
            "user_id": self.user_id.id,
            "company_id": self.company1.id,
        }
        self.user_id.write({"role_line_ids": [(0, 0, line1_vals)]})
        line2_vals = {
            "role_id": self.role2_id.id,
            "user_id": self.user_id.id,
            "company_id": self.company2.id,
        }

        self.user_id.write({"role_line_ids": [(0, 0, line2_vals)]})
        self.assertEqual(self.user_id.profile_ids, self.profile1_id)

        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        expected_group_ids = sorted(set(self.role1_group_ids))
        self.assertEqual(user_group_ids, expected_group_ids)

        self.user_id.company_id = self.company2
        self.assertEqual(self.user_id.profile_ids, self.profile2_id)
        user_group_ids = sorted(
            set([group.id for group in self.user_id.groups_id])
        )
        expected_group_ids = sorted(set(self.role2_group_ids))
        self.assertEqual(user_group_ids, expected_group_ids)
