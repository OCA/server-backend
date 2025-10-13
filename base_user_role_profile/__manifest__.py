# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "User profiles",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base_user_role", "web"],
    "post_init_hook": "post_init_hook",
    "data": [
        "data/res_users_profile_data.xml",
        "security/ir.model.access.csv",
        "views/res_users_views.xml",
        "views/res_users_profile_views.xml",
        "views/res_users_role_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_user_role_profile/static/src/**/*",
        ],
    },
    "installable": True,
}
