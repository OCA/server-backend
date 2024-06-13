{
    "name": "User management Group",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "Le Filament, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "development_status": "Beta",
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base", "auth_signup"],
    "data": [
        "security/res_groups.xml",
        "security/ir_ui_menu.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
