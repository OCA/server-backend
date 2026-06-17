# Copyright 2026 CIT Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Base User Role Extended",
    "version": "18.0.1.0.0",
    "summary": "Adds Menu Item ACL control to User Roles",
    "author": "CIT Services, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base_user_role",
        "mail",
    ],
    "data": [
        "views/res_role_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "license": "AGPL-3",
}
