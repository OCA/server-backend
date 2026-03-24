# Copyright 2026 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base User Role Menu",
    "summary": "List roles required to access each menu item",
    "version": "14.0.1.0.0",
    "category": "security",
    "website": "https://github.com/OCA/server-backend",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "maintainers": ["Kev-Roche"],
    "application": False,
    "installable": True,
    "depends": [
        "base_user_role",
    ],
    "data": [
        "views/ir_ui_menu.xml",
        "views/res_users_role.xml",
    ],
}
