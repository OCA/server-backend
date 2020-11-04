# Copyright 2020 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO customer_global_discount_rel
            (partner_id, global_discount_id)
            SELECT
                partner_id,
                global_discount_id
            FROM
                global_discount_res_partner_rel
            WHERE
                discount_scope = 'sale';
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO supplier_global_discount_rel
            (partner_id, global_discount_id)
            SELECT
                partner_id,
                field_id
            FROM
                global_discount_res_partner_rel
            WHERE
                discount_scope = 'purchase';
        """,
    )
