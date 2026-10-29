# Copyright (C) 2026 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Fill the new `company_ids` (Many2many) relation table from the values
    # `pre-migrate.py` preserved under `company_id_old`, then drop it.
    openupgrade.m2o_to_x2m(
        env.cr,
        env["res.users.role.line"],
        "res_users_role_line",
        "company_ids",
        "company_id_old",
    )
    openupgrade.drop_columns(env.cr, [("res_users_role_line", "company_id_old")])
