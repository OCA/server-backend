# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Caldav and Carddav support",
    "version": "12.0.1.0.0",
    "author": "initOS GmbH, Therp BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "summary": "Access Odoo data as calendar or address book",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base",
    ],
    "demo": [
        "demo/dav_collection.xml",
    ],
    "data": [
        "views/dav_collection.xml",
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {
        "python": ["radicale"],
    },
}
