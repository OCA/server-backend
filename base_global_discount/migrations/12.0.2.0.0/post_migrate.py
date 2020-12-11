# Copyright 2020 David Vidal
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from openupgradelib.openupgrade import migrate


@migrate()
def migrate(env, version):
    """Put all partner managers as global discount managers"""
    users = env.ref("base.group_partner_manager").users
    env.ref("base_global_discount.group_global_discount").users = users
