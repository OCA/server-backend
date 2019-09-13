# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Caldav and Carddav support",
    "version": "11.0.1.0.0",
    "author": "initOS GmbH,Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "summary": "Access Odoo data as calendar or address book",
    "depends": [
        'base',
        # TODO: this is only for demoing during development, remove
        # when done (and the collection in demo data)
        'calendar',
    ],
    "demo": [
        "demo/dav_collection.xml",
    ],
    "data": [
        "views/dav_collection.xml",
        'security/ir.model.access.csv',
    ],
    "external_dependencies": {
        'python': ['radicale'],
    },
}
