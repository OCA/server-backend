# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Model Access Restriction",
    "summary": "New type of access rule to restrict permissions based on groups",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-backend",
    "author": "Sygel, Odoo Community Association (OCA)",
    "maintainers": ["tisho99"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ir_model_access_restriction_views.xml",
    ],
}
