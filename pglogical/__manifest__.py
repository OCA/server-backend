# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "pglogical",
    "summary": "Support for replicating Odoo's database",
    "version": "12.0.1.0.1",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "post_load": "post_load",
    'external_dependencies': {
        'python': ['sqlparse'],
    },
}
