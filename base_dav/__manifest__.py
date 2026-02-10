# Copyright 2018 Therp BV <https://therp.nl>
# Copyright 2019-2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Caldav and Carddav support",
    "version": "17.0.1.0.0",
    "author": "initOS GmbH,Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "summary": "Access Odoo data as calendar or address book",
    "depends": [
        'base',
    ],
    # Demo data removed for Odoo 17 compatibility (field xmlids no longer exist).
    "data": [
        "views/dav_collection.xml",
        "views/res_users.xml",
        'security/ir.model.access.csv',
    ],
    "assets": {
        "web.assets_backend": [
            "base_dav/static/src/js/carddav_copy.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "external_dependencies": {
        'python': ['radicale', 'vobject'],
    },
}
