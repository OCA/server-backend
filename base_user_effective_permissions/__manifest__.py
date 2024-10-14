# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Effective permissions",
    "summary": "Inspect effective permissions applying to a user",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Technical",
    "website": "https://github.com/OCA/server-backend",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users_effective_permission.xml",
        "views/res_users.xml",
    ],
}
