# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "External API Client",
    "version": "15.0.1.0.0",
    "license": "LGPL-3",
    "summary": """
        API Client for REST integrations and OAuth authorization
    """,
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/server-backend",
    "category": "server",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/apicli_connection_view.xml",
        "views/apicli_document_view.xml",
        "views/res_partner_view.xml",
        "views/apicli_message.xml",
        "demo/api_document_demo.xml",
    ],
    "demo": [],
    "installable": True,
}
