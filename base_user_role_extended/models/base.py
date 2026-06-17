# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models
from odoo.tools import config

_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = "base"

    def _role_policy_untouchable_groups(self):
        """
        The role policy will remove all groups from the fields
        except the ones defined in this method.
        """
        return [
            "base.group_no_one",
            "base.group_user",
            "base.group_erp_manager",
            "base.group_system",
            "base.group_portal",
            "base.group_public",
        ]

    def _get_role_policy_group_keep_ids(self):
        group_user = self.env.ref("base.group_user")
        keep_ids = [
            self.env.ref(x).id for x in self._role_policy_untouchable_groups()
        ] + [group_user.id]
        return keep_ids

    @api.model
    def user_has_groups(self, groups):
        """
        Disable no-role groups except for user_admin & user_root.
        """
        user = self.env.user
        if (
            user.exclude_from_role_policy
            or user == self.env.ref("base.public_user")
            or config.get("test_enable")
        ):
            return super().user_has_groups(groups)

        role_groups = []
        for group_ext_id in groups.split(","):
            xml_id = group_ext_id[0] == "!" and group_ext_id[1:] or group_ext_id
            if xml_id in self._role_policy_untouchable_groups():
                role_groups.append(group_ext_id)
            else:
                group = self.env.ref(xml_id)
                if group.role:
                    role_groups.append(group_ext_id)
        if not role_groups:
            return True
        else:
            return super().user_has_groups(",".join(role_groups))
