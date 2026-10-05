# Copyright 2026 Ross Golder
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Native CalDAV/CardDAV server",
    "summary": "CalDAV and CardDAV endpoint served directly by Odoo",
    "version": "17.0.1.0.0",
    "category": "Extra Tools",
    "author": "Ross Golder",
    "license": "AGPL-3",
    "website": "https://github.com/rossigee/server-backend",
    "depends": [
        "base_dav",
        "calendar",
        "contacts",
    ],
    "external_dependencies": {
        "python": [
            "icalendar",
            "vobject",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/dav_collection.xml",
        "views/calendar_event.xml",
        "data/ir_cron.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
