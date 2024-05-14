# Copyright 2024 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Base External System - Microsoft Client Assertion",
    "summary": "Connect to external systems through Microsoft Client Assertion.",
    "version": "16.0.1.0.0",
    "category": "Base",
    "website": "https://github.com/OCA/server-backend",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "maintainers": ["NL66278"],
    "license": "AGPL-3",
    "depends": [
        "base_external_system_oauth",
    ],
    "data": [
        "demo/auth_oauth_provider_demo.xml",
        "demo/external_system_demo.xml",
    ],
    "external_dependencies": {"python": ["msal"]},
    "application": False,
    "installable": True,
}
