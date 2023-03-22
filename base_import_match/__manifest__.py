# Copyright 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Base Import Match",
    "summary": "Try to avoid duplicates before importing",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Tecnativa, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["base_import"],
    "data": [
        "security/ir.model.access.csv",
        "data/base_import_match.xml",
        "views/base_import_match_view.xml",
    ],
    "demo": ["demo/base_import_match.xml"],
}
