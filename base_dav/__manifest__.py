# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "DAV support",
    "version": "17.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Access Odoo data as calendar, addressbook, or attached files via WebDAV",
    "author": "Therp BV,initOS GmbH,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "summary": "Access Odoo data as calendar, addressbook, or attached files via WebDAV",
    "development_status": "Beta",
    "depends": [
        "base",
        "calendar",
        "mail",
    ],
    "demo": [
        "demo/dav_collection.xml",
    ],
    "external_dependencies": {
        "python": [
            "pytz",
            "vobject",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/dav_collection.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "installable": True,
}
