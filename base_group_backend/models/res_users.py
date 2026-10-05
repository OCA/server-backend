import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


ROLE_GROUP_MAP = {
    "group_backend": "base_group_backend.base_group_backend",
    "group_backend_ui": "base_group_backend.group_backend_ui_users",
    "group_system": "base.group_system",
    # Keep this mapping at the last position:
    # _compute_role relies on this order,
    # as _has_group accept this for the backend groups
    "group_user": "base.group_user",
}


class Users(models.Model):
    _inherit = "res.users"

    role = fields.Selection(
        selection_add=[
            ("group_backend", "Backend User"),
            ("group_backend_ui", "Backend User UI"),
        ]
    )

    @api.model
    def _has_group(self, group_ext_id):
        """While ensuring a user is part of `base.group_user` this code will
        try if user is in the `base_group_backend.group_backend` group to let access
        to the odoo backend.

        This code avoid to overwrite a lot of places in controllers from
        different modules ('portal', 'web', 'base') with hardcoded statement
        that check if user is part of `base.group_user` group.

        As far `base.group_user` have a lot of default permission this
        makes hard to maintain proper access right according your business.
        """
        res = super()._has_group(group_ext_id)
        if not res and (group_ext_id == "base.group_user"):
            has_base_group_backend = super()._has_group(
                "base_group_backend.base_group_backend"
            ) or super()._has_group("base_group_backend.group_backend_ui_users")
            if has_base_group_backend:
                _logger.debug(
                    "Forcing has_group to return True"
                    + " for base_group_backend and base_group_backend_ui_users"
                )
            return has_base_group_backend
        return res

    @api.depends("all_group_ids")
    def _compute_share(self):
        res = super()._compute_share()
        backend_user_group_id = self.env["ir.model.data"]._xmlid_to_res_id(
            "base_group_backend.base_group_backend"
        )
        backend_ui_user_group_id = self.env["ir.model.data"]._xmlid_to_res_id(
            "base_group_backend.group_backend_ui_users"
        )
        internal_users = self.filtered_domain(
            [("group_ids", "in", [backend_user_group_id, backend_ui_user_group_id])]
        )
        internal_users.share = False
        return res

    @api.depends("group_ids")
    def _compute_role(self):
        for user in self:
            role = False
            for role_key, group_ext_id in ROLE_GROUP_MAP.items():
                if user.has_group(group_ext_id):
                    role = role_key
                    break
            user.role = role

    @api.onchange("role")
    def _onchange_role(self):
        groups = {}
        for role_key, group_ext_id in ROLE_GROUP_MAP.items():
            groups[role_key] = self.env["res.groups"].new(
                origin=self.env.ref(group_ext_id)
            )
        _logger.info("Role to group mapping: %s", groups)
        for user in self:
            if user.role:
                group_ids = user.group_ids - sum(
                    groups.values(), self.env["res.groups"].browse()
                )
                user.group_ids = group_ids + groups[user.role]
