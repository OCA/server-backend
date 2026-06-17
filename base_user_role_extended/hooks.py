# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """
    Remove groups from menuitems, views, actions and users since the standard groups
    are replaced by role groups when installing this module.
    """
    env = api.Environment(
        cr, SUPERUSER_ID, {"active_test": False, "role_policy_init": True}
    )
    menus = env["ir.ui.menu"].search([])
    menus.write({"groups_id": [(5,)]})