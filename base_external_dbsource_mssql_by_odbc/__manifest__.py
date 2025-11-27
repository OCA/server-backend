# Copyright (C) 2025 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "External Database Source - MSSQL By ODBC",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "development_status": "Beta",
    "maintainers": ["max3903", "Nikul-OSI"],
    "website": "https://github.com/OCA/server-backend",
    "license": "LGPL-3",
    "depends": ["base_external_dbsource_mssql"],
    "external_dependencies": {"python": ["pyodbc"]},
    "demo": ["demo/base_external_dbsource.xml"],
    "installable": True,
}
