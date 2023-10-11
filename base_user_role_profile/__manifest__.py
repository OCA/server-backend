# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "User profiles",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base_user_role", "web"],
    "post_init_hook": "post_init_hook",
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/user.xml",
        "views/role.xml",
        "views/profile.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_user_role_profile/static/src/js/switch_profile_menu.js",
        ],
    },
    "qweb": ["static/src/xml/templates.xml"],
    "installable": True,
}
