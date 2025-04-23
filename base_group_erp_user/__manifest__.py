# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base Group Erp User",
    "summary": """
        This module adds a new group in security management category.
        This group allows users to have basic features such as user
        or group creation. But they can't change groups associated to
        a group or groups associated to a user""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base",
    ],
    "data": [
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "security/ir_module_category.xml",
        "security/ir_rule.xml",
        "security/res_users.xml",
        "views/menus.xml",
    ],
    "demo": [],
}
