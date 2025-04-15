# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import UserError

from .common import TestBaseUserGroupMgmtCommon


class TestBaseUserGroupMgmt(TestBaseUserGroupMgmtCommon):
    def test_workflow_approve(self):
        request = self.request
        approver_1 = self.approver_1
        approver_2 = self.approver_2
        request.with_user(
            self.user.id,
        ).action_confirm()
        self.assertEqual(request.state, "first_approval")

        with self.assertRaises(UserError) as e:
            request.with_user(
                self.user.id,
            ).action_first_approval()
        self.assertIn("You can't approve this request", e.exception.args[0])

        request.with_user(approver_1).action_first_approval()
        self.assertEqual(request.state, "second_approval")
        self.assertEqual(request.approver_1_user_id, approver_1)

        with self.assertRaises(UserError) as e:
            request.with_user(
                approver_1,
            ).action_second_approval()
        self.assertIn("You can't approve this request", e.exception.args[0])

        request.with_user(approver_2).action_second_approval()
        self.assertEqual(request.state, "approved")
        self.assertEqual(request.approver_2_user_id, approver_2)

    def test_workflow_reject(self):
        request = self.request
        approver_1 = self.approver_1
        request.with_user(
            self.user.id,
        ).action_confirm()
        self.assertEqual(request.state, "first_approval")
        request.with_user(approver_1).action_reject()
        self.assertEqual(request.state, "rejected")

    def test_workflow_from_approver(self):
        request = self.request
        approver_1 = self.approver_1
        approver_2 = self.approver_2

        request.sudo().write(
            {
                "user_id": approver_1.id,
            }
        )
        request.with_user(
            approver_1,
        ).action_confirm()
        self.assertEqual(request.state, "first_approval")

        with self.assertRaises(UserError) as e:
            request.with_user(
                approver_1,
            ).action_first_approval()
        self.assertIn("You can't approve this request", e.exception.args[0])

        request.with_user(approver_2).action_first_approval()
        self.assertEqual(request.state, "second_approval")
        self.assertEqual(request.approver_1_user_id, approver_2)

        with self.assertRaises(UserError) as e:
            request.with_user(
                approver_1,
            ).action_second_approval()
        self.assertIn("You can't approve this request", e.exception.args[0])

    def test_workflow_super_approver(self):
        request = self.request
        approver_1 = self.approver_1
        approver_2 = self.approver_2

        request.sudo().write(
            {
                "user_id": approver_2.id,
            }
        )
        request.with_user(
            approver_2,
        ).action_confirm()
        self.assertEqual(request.state, "second_approval")
        self.assertEqual(request.approver_1_user_id, approver_2)

        with self.assertRaises(UserError) as e:
            request.with_user(
                approver_2,
            ).action_second_approval()
        self.assertIn("You can't approve this request", e.exception.args[0])

        request.with_user(approver_1).action_second_approval()
        self.assertEqual(request.state, "approved")
        self.assertEqual(request.approver_2_user_id, approver_1)

    def test_user_add_group(self):
        request = self.request
        user = self.user_1
        group = self.group_1
        self.assertNotIn(group, user.groups_id)
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "user_add_group",
                "group_1_ids": [Command.set(group.ids)],
                "user_ids": [Command.set(user.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertIn(group, user.groups_id)

    def test_user_remove_group(self):
        request = self.request
        user = self.user_1
        group = self.group_1
        user.write(
            {
                "groups_id": [Command.link(group.id)],
            }
        )
        self.assertIn(group, user.groups_id)
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "user_remove_group",
                "group_1_ids": [Command.set(group.ids)],
                "user_ids": [Command.set(user.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertNotIn(group, user.groups_id)

    def test_group_add_group(self):
        request = self.request
        group_1 = self.group_1
        group_2 = self.group_2
        self.assertNotIn(group_2, group_1.implied_ids)
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "group_add_group",
                "group_1_ids": [Command.set(group_1.ids)],
                "group_2_ids": [Command.set(group_2.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertIn(group_2, group_1.implied_ids)

    def test_group_remove_group(self):
        request = self.request
        group_1 = self.group_1
        group_2 = self.group_2
        group_1.write(
            {
                "implied_ids": [Command.link(group_2.id)],
            }
        )
        self.assertIn(group_2, group_1.implied_ids)
        line = self.RequestLine.create(
            {
                "request_id": request.id,
                "action": "group_remove_group",
                "group_1_ids": [Command.set(group_1.ids)],
                "group_2_ids": [Command.set(group_2.ids)],
            }
        )
        self.assertTrue(bool(line.name))
        self._do_updates(request)
        self.assertNotIn(group_2, group_1.implied_ids)
