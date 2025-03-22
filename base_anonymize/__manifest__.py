# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Anonymize a database",
    "summary": "Overwrite all privacy relevant data in a database",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "data/anonymize_field.xml",
        "data/anonymize.method.fictional.character.data.csv",
        "security/ir.model.access.csv",
        "views/anonymize_field.xml",
        "wizards/anonymize_wizard.xml",
        "views/menu.xml",
    ],
}
