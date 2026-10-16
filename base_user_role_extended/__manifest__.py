# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Base User Role Extended",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "summary": "Extends user roles with additional access control features",
    "author": "CIT Services, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "LGPL-3",
    "depends": ["base_user_role"],
    "data": [
        "views/res_users_views.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
