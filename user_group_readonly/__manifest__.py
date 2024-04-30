# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Readonly access to everything",
    "summary": "Add a group that has readonly access to all of Odoo",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Extra Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "depends": [
        "mail",
    ],
    "data": [
        "data/res_groups.xml",
        "data/ir_cron.xml",
    ],
}
