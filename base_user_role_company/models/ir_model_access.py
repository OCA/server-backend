# Copyright (C) 2026 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, tools
from odoo.tools import SQL


class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    @tools.ormcache("self.env.uid", "mode", "tuple(self.env.companies.ids)")
    def _get_allowed_models(self, mode="read"):
        """ORM override WITHOUT calling super(), else it returns parent cache.
        We add 'self.env.companies.ids' in @tools.ormcache.
        To keep synched with: addons/base/models/ir_model::_get_allowed_models"""
        assert mode in ("read", "write", "create", "unlink"), "Invalid access mode"

        group_ids = self.env.user._get_group_ids()
        self.flush_model()
        rows = self.env.execute_query(
            SQL(
                """
            SELECT m.model
              FROM ir_model_access a
              JOIN ir_model m ON (m.id = a.model_id)
             WHERE a.perm_%s
               AND a.active
               AND (
                    a.group_id IS NULL OR
                    a.group_id IN %s
                )
            GROUP BY m.model
        """,
                SQL(mode),
                tuple(group_ids) or (None,),
            )
        )

        return frozenset(v[0] for v in rows)
