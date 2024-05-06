# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Readonly publishing of calendars",
    "summary": "Provide (readonly) .ics URLs to calendar-like models",
    "version": "15.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "external_dependencies": {
        "python": ["vobject"],
    },
    "depends": [
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/base_ical.xml",
        "views/res_users.xml",
    ],
    "demo": [
        "demo/base_ical.xml",
    ],
}
