# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Base External Dbsource Importer",
    "summary": "Import data from external DB Sources",
    "version": "18.0.1.0.1",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["base_external_dbsource", "base_location", "base_vat"],
    "external_dependencies": {"python": ["sqlalchemy"]},
    "data": ["security/ir.model.access.csv", "views/base_external_dbsource_view.xml"],
}
