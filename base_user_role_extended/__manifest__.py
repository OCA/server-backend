# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Base User Role Extended",
    "version": "18.0.1.0.0",
    "summary": "Extends user roles with additional access control features",
    "author": "CIT Services, Odoo Community Association (OCA)",
    "company": "CIT Services",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base_user_role",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users_role_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
