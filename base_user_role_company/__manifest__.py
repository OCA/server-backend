# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "User roles by company",
    "version": "19.0.2.1.0",
    "category": "Tools",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base_user_role"],
    "external_dependencies": {"python": ["openupgradelib"]},
    "data": [
        "views/role.xml",
        "views/user.xml",
    ],
    "installable": True,
    "maintainer": "dreispt",
    "development_status": "Beta",
}
