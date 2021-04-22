# Copyright 2020 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Easy Massive Translation",
    "summary": "Import terms translations in multiple languages",
    "version": "13.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-tools",
    "author": "Sygel, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["base"],
    "data": [
        "wizards/import_massive_translation_view.xml",
        "wizards/export_massive_translation_view.xml",
        "wizards/easy_massive_translation_menus.xml",
    ],
}
