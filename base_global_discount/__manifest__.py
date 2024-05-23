# Copyright 2019 Tecnativa S.L. - David Vidal
# Copyright 2020 Xtendoo - Manuel Calero
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Base Global Discount",
    "version": "16.0.1.1.0",
    "category": "Base",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/server-backend",
    "license": "AGPL-3",
    "depends": ["product"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/global_discount_views.xml",
        "views/product_views.xml",
        "views/res_partner_views.xml",
    ],
    "application": False,
    "installable": True,
}
