# Copyright 2025 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "External Database Source - DuckDB",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "LGPL-3",
    "depends": ["base_external_dbsource"],
    "external_dependencies": {"python": ["duckdb"]},
    "demo": ["demo/base_external_dbsource_demo.xml"],
    "data": ["views/base_external_dbsource_views.xml"],
    "installable": True,
}
