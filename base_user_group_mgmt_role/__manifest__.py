# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base User Group Management Role",
    "summary": """
        Add role features in security management module""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base_user_role",
        "base_user_group_mgmt",
    ],
    "data": [
        "views/base_security_update_request_line.xml",
    ],
    "demo": [],
}
