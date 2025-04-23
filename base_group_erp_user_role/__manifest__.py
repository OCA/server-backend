# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base Group Erp User Role",
    "summary": """
        This module implements the role security around the ERP user group
        to make sensitive data readonly (user roles, group's roles, etc).""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base_group_erp_user",
        "base_user_role",
    ],
    "data": [
        "security/res_users_role.xml",
        "security/res_users_role_line.xml",
    ],
    "demo": [],
}
