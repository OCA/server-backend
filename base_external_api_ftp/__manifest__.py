# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "External API Client for FTP",
    "version": "15.0.1.0.0",
    "license": "LGPL-3",
    "summary": "API Client for API Integrations",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainers": ["dreispt"],
    "website": "https://github.com/OCA/server-backend",
    "category": "server",
    "depends": ["base_external_api"],
    "external_dependencies": {
        "python": ["pysftp"],
    },
    "demo": [
        "demo/api_connection_ftp_demo.xml",
        "demo/api_connection_ftp_data.xml",
    ],
    "installable": True,
}
