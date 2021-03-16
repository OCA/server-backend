# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _affect_group_to_category(env):
    _logger.info("Set Category 'User roles' to groups related to roles")
    roles = env["res.users.role"].search([])
    groups = roles.mapped("group_id").filtered(lambda x: not x.category_id)
    user_role_category = env.ref("base_user_role.ir_module_category_role")
    groups.write({"category_id": user_role_category.id})


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        _affect_group_to_category(env)
