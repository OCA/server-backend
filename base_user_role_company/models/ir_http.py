# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(IrHttp, self).session_info()
        cids = request.httprequest.cookies.get("cids", str(self.env.company.id))
        cids = [int(cid) for cid in cids.split(",")]
        fetch_all_role_lines = self.env.user.role_line_ids.search(
            ["|", ("active_role", "=", True), ("active_role", "=", False)]
        )
        fetch_all_role_lines.write({"active_role": True})
        cid = cids[0]
        role_lines = None
        if not len(cids) > 1:
            role_lines = self.env.user.role_line_ids.search(
                [("company_id", "!=", None), ("company_id", "!=", cid)]
            )
        else:
            default_role = self.env.user.role_line_ids.search(
                [("company_id", "=", None)]
            )
            if default_role:
                role_lines = self.env.user.role_line_ids.search(
                    [("company_id", "!=", None)]
                )
            else:
                role_lines = self.env.user.role_line_ids.search(
                    [("company_id", "!=", cid)]
                )
        if role_lines:
            role_lines.write({"active_role": False})
            self.env.user.set_groups_from_roles()
        return result
