# Copyright 2021 Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Group backend",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "author": "Pierre Verkest, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/server-backend",
    "depends": [
        "base",
        "base_install_request",  # weird module, we need to survive with it
        "mail",
    ],
    "maintainers": ["FranzPoize", "bealdav"],
    "demo": [
        "demo/test-model.xml",
        "demo/ir.model.access.csv",
        "demo/backend_dummy_model.xml",
        "demo/res_partners.xml",
        "demo/res_users.xml",
    ],
    "data": [
        "data/res_groups.xml",
        "data/ir_ui_menu.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
