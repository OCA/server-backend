# Copyright (C) 2026 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

# `res.users.role.line.company_id` (Many2one) becomes `company_ids`
# (Many2many): rename the old column out of the way before the ORM
# drops it, so `post-migrate.py` can use it to fill the new relation table.
_COLUMN_RENAMES = {
    "res_users_role_line": [
        ("company_id", "company_id_old"),
    ],
}


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _COLUMN_RENAMES)
