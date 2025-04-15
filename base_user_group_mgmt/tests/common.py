# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import Command
from odoo.tests.common import TransactionCase


class TestBaseUserGroupMgmtCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Request = cls.env["base.security.update.request"]
        cls.RequestLine = cls.env["base.security.update.request.line"]
        cls.User = cls.env["res.users"].with_context(no_reset_password=True)
        cls.Group = cls.env["res.groups"]

        cls.group_user = cls.env.ref("base_user_group_mgmt.security_management_user")
        cls.group_approver = cls.env.ref(
            "base_user_group_mgmt.security_management_approver"
        )
        cls.group_super_approver = cls.env.ref(
            "base_user_group_mgmt.security_management_super_approver"
        )
        cls.group_manager = cls.env.ref(
            "base_user_group_mgmt.security_management_manager"
        )
        cls.category_hidden = cls.env.ref("base.module_category_hidden")

        cls.user = cls.User.create(
            {
                "name": "user",
                "login": "user",
                "groups_id": [
                    Command.set(cls.group_user.ids),
                ],
            }
        )

        cls.approver_1 = cls.User.create(
            {
                "name": "Approver 1",
                "login": "approver1",
                "groups_id": [
                    Command.set(cls.group_approver.ids),
                ],
            }
        )

        cls.approver_2 = cls.User.create(
            {
                "name": "Approver 2",
                "login": "approver2",
                "groups_id": [
                    Command.set(cls.group_super_approver.ids),
                ],
            }
        )

        cls.user_1 = cls.User.create(
            {
                "name": "Test user",
                "login": "testuser",
            }
        )

        cls.group_1 = cls.Group.create(
            {
                "name": "Test group 1",
                "category_id": cls.category_hidden.id,
            }
        )

        cls.group_2 = cls.Group.create(
            {
                "name": "Test group 2",
                "category_id": cls.category_hidden.id,
            }
        )

        cls.request = cls.Request.create(
            {
                "user_id": cls.user.id,
            }
        )

    def _do_updates(self, request):
        request.write({"state": "approved"})
        request.sudo().line_ids._do_updates()
