# Copyright (C) 2021 Daniel Reis
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Pip Install Odoo Modules",
    "version": "14.0.1.0.0",
    "category": "Tools",
    "author": "Daniel Reis, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/base_module_pip_install_views.xml",
    ],
    "installable": True,
    "maintainers": ["dreispt"],
    "development_status": "Beta",
}
