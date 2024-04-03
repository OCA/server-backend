# Copyright 2017 LasLabs Inc.
# Copyright 2024 Therp BV <https://therp.nl>.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Base External System",
    "summary": "Data models allowing for connection to external systems.",
    "version": "16.0.1.0.0",
    "category": "Base",
    "website": "https://github.com/OCA/server-backend",
    "author": "LasLabs, Therp BV, Odoo Community Association (OCA)",
    "maintainers": ["NL66278"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["base"],
    "data": [
        "demo/external_system_os_demo.xml",
        "security/ir.model.access.csv",
        "views/external_system_view.xml",
        "views/ir_ui_menu.xml",
    ],
}
