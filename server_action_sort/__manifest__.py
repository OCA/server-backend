# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Server Actions - Mass Sort Lines",
    "version": "16.0.1.0.0",
    "author": "GRAP, " "Odoo Community Association (OCA)",
    "summary": "Sort any lines of any models by any criterias",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "license": "AGPL-3",
    "depends": ["base"],
    "maintainers": ["legalsylvain"],
    "data": [
        "security/ir.model.access.csv",
        "views/view_ir_actions_server.xml",
    ],
    "demo": ["demo/ir_actions_server.xml"],
}
