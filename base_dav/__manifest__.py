# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "CalDAV and CardDAV support",
    "version": "17.0.1.0.0",
    "author": "initOS GmbH,Therp BV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "summary": "Access Odoo data as calendar or address book",
    "development_status": "Beta",
    "depends": [
        "base",
        "calendar",
    ],
    "demo": [
        "demo/dav_collection.xml",
    ],
    "data": [
        "views/dav_collection.xml",
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {
        "python": [
            "radicale",
            "vobject",
            "dateutil",
        ],
    },
    "application": True,
    "auto_install": False,
    "installable": True,
}
