# Copyright 2022 Tecnativa - Sergio Teruel
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "External Database Source - SAP - Hana",
    "version": "15.0.1.0.0",
    "category": "Tools",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "LGPL-3",
    "depends": ["base_external_dbsource"],
    "external_dependencies": {"python": ["sqlalchemy", "sqlalchemy-hana", "hdbcli"]},
    "demo": ["demo/base_external_dbsource.xml"],
    "installable": True,
}
