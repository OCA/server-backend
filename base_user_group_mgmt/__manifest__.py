# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Base User Group Management",
    "summary": """
        This modules allows to have a validation of users and groups update.
        Views related to security models become readonly and each update
        of user's groups or groups is done after the workflow of a
        dedicated model is approved.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/res_groups.xml",
        "security/base_security_update_request.xml",
        "security/base_security_update_request_line.xml",
        "views/base_security_update_request_line.xml",
        "views/base_security_update_request.xml",
        "views/ir_model_access.xml",
        "views/ir_rule.xml",
    ],
    "demo": [],
    "post_init_hook": "_post_init_hook",
}
