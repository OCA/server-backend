from odoo import api, models


class Users(models.Model):
    _inherit = "res.users"

    @api.model
    def has_group(self, group_ext_id):
        """While ensuring a user is part of `base.group_user` this code will
        try if user is in the `group_backend.group_backend` group to let access
        to the odoo backend.

        This code avoid to overwrite a lot of places in controllers from
        different modules ('portal', 'web', 'base') with hardcoded statement
        that check if user is part of `base.group_user` group.

        As far `base.group_user` have a lot of default permission this
        makes hard to maintain proper access right according your business.
        """
        res = super(Users, self).has_group(group_ext_id)
        if not res and group_ext_id == "base.group_user":
            return super(Users, self).has_group("group_backend.group_backend")
        return res
