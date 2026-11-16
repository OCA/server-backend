# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class TestUserProfile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role_model = cls.env["res.users.role"]

        cls.user_id = new_test_user(
            cls.env, login="user_test_roles", name="USER TEST (ROLES)"
        )

        cls.profile1_id = cls.env["res.users.profile"].create({"name": "profile1"})
        cls.profile2_id = cls.env["res.users.profile"].create({"name": "profile2"})

        # role 1
        cls.group_user_id = cls.env.ref("base.group_user")
        cls.group_no_one_id = cls.env.ref("base.group_no_one")

        # role 2
        cls.group_system_id = cls.env.ref("base.group_system")
        cls.group_multi_company_id = cls.env.ref("base.group_multi_company")

        # role 3
        cls.group_erp_manager_id = cls.env.ref("base.group_erp_manager")
        cls.group_partner_manager_id = cls.env.ref("base.group_partner_manager")

        # roles 1 and 2 have a profile, role 3 no profile
        vals = {
            "name": "ROLE_1",
            "implied_ids": [
                fields.Command.set([cls.group_user_id.id, cls.group_no_one_id.id])
            ],
            "profile_id": cls.profile1_id.id,
        }
        cls.role1_id = cls.role_model.create(vals)
        cls.role1_group_ids = cls._helper_unpack_groups_role(cls.role1_id)

        vals = {
            "name": "ROLE_2",
            "implied_ids": [
                fields.Command.set(
                    [cls.group_system_id.id, cls.group_multi_company_id.id]
                )
            ],
            "profile_id": cls.profile2_id.id,
        }
        cls.role2_id = cls.role_model.create(vals)
        cls.role2_group_ids = cls._helper_unpack_groups_role(cls.role2_id)

        vals = {
            "name": "ROLE_3",
            "implied_ids": [
                fields.Command.set(
                    [cls.group_erp_manager_id.id, cls.group_partner_manager_id.id]
                )
            ],
        }
        cls.role3_id = cls.role_model.create(vals)
        cls.role3_group_ids = cls._helper_unpack_groups_role(cls.role3_id)

    @staticmethod
    def _helper_unpack_groups_role(role):
        role_group_ids = role.all_implied_ids.ids
        return sorted(set(role_group_ids))

    @staticmethod
    def _helper_unpack_groups_group(group):
        group_ids = group.all_implied_ids.ids
        group_ids.append(group.id)
        return sorted(set(group_ids))

    def test_filter_by_profile(self):
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role1_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role2_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.assertEqual(self.user_id.profile_ids, self.profile1_id + self.profile2_id)
        self.assertEqual(self.user_id.profile_id, self.profile1_id)
        self.assertFalse(self.user_id.restrict_profile_switching)
        self.user_id.action_profile_change({"profile_id": self.profile1_id.id})

        user_group_ids = sorted({group.id for group in self.user_id.group_ids})
        expected_group_ids = sorted(set(self.role1_group_ids))
        self.assertEqual(user_group_ids, expected_group_ids)

        self.assertFalse(self.user_id.restrict_profile_switching)
        self.user_id.action_profile_change({"profile_id": self.profile2_id.id})

        user_group_ids = sorted({group.id for group in self.user_id.group_ids})
        expected_group_ids = sorted(set(self.role2_group_ids))
        self.assertEqual(user_group_ids, expected_group_ids)

    def test_restrict_profile_switching(self):
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role1_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role2_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.assertEqual(self.user_id.profile_id, self.profile1_id)
        self.user_id.restrict_profile_switching = True
        self.assertTrue(self.user_id.restrict_profile_switching)
        self.user_id.action_profile_change({"profile_id": self.profile2_id.id})
        self.assertEqual(self.user_id.profile_id, self.profile1_id)

    def test_allow_by_noprofile(self):
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role1_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role3_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.assertFalse(self.user_id.include_default_profile)
        self.assertEqual(self.user_id.profile_ids, self.profile1_id)
        user_group_ids = []
        for group in self.user_id.group_ids:
            user_group_ids += self._helper_unpack_groups_group(group)
        user_group_ids = set(user_group_ids)
        expected_groups = set(self.role1_group_ids + self.role3_group_ids)
        self.assertEqual(user_group_ids, expected_groups)

    def test_include_default_profile(self):
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role1_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role3_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.user_id.write({"include_default_profile": True})
        self.assertTrue(self.user_id.include_default_profile)
        self.assertEqual(
            self.user_id.profile_ids,
            self.user_id._get_default_profile() + self.profile1_id,
        )

    def test_update_profile_id(self):
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role1_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.user_id.write(
            {
                "role_line_ids": [
                    fields.Command.create(
                        {"role_id": self.role3_id.id, "user_id": self.user_id.id}
                    )
                ]
            }
        )
        self.assertFalse(self.user_id.include_default_profile)
        self.user_id.profile_ids = False
        self.user_id._update_profile_id()
        self.assertEqual(self.user_id.profile_id, self.profile1_id)
        self.user_id.write({"include_default_profile": True})
        self.user_id.profile_id = False
        self.user_id._update_profile_id()
        self.assertEqual(self.user_id.profile_id, self.user_id._get_default_profile())
