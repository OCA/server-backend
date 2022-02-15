# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """
        Based on the selected companies (cids),
        calculate the roles to enable.
        A role should be enabled only when it applies to all selected companies.
        """
        result = super(IrHttp, self).session_info()
        if self.env.user.role_line_ids:
            cids_str = request.httprequest.cookies.get("cids", str(self.env.company.id))
            cids = [int(cid) for cid in cids_str.split(",")]
            # The first element of cids is the currently selected company
            self.env.user.set_groups_from_roles(company_id=cids[0])
        return result
