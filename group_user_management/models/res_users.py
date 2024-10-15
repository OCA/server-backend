#  Copyright (c) 2024- Le Filament (https://le-filament.com)
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = "res.users"

    def _remove_reified_groups(self, values):
        """
        Overrides default base module method to raise an AccessError in case user tries
        to set/unset base.group_system or base.group_erp_manager from another user
        if current user is not at least in base.group_erp_manager
        """
        res = super()._remove_reified_groups(values)
        if (
            "groups_id" in res
            and not self.env.user._is_admin()
            and not self.env.user._is_system()
            and not self.env.user._is_superuser()
        ):
            admin_group = self.env.ref("base.group_erp_manager")
            system_group = self.env.ref("base.group_system")
            groups = res.get("groups_id")
            if groups and any(
                group == (3, admin_group.id) or group == (3, system_group.id)
                for group in groups
            ):
                raise AccessError(
                    _(
                        "You are not allowed to unset an Administration group on admin user"
                    )
                )
            elif groups and any(
                group == (4, admin_group.id) or group == (4, system_group.id)
                for group in groups
            ):
                raise AccessError(
                    _(
                        "You are not allowed to set an Administration group on non-admin user"
                    )
                )
        return res
