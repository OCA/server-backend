# Copyright 2020 Tecnativa - Ernesto Tejeda
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO customer_global_discount_rel
        (partner_id, global_discount_id)
        SELECT rel.partner_id, rel.global_discount_id
        FROM global_discount_res_partner_rel rel
        JOIN global_discount gd ON gd.id = rel.global_discount_id
        WHERE gd.discount_scope = 'sale';
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO supplier_global_discount_rel
        (partner_id, global_discount_id)
        SELECT rel.partner_id, rel.global_discount_id
        FROM global_discount_res_partner_rel rel
        JOIN global_discount gd ON gd.id = rel.global_discount_id
        WHERE gd.discount_scope = 'purchase';
        """,
    )
