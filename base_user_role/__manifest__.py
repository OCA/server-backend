# Copyright 2014 ABF OSIELL <http://osiell.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


{
    "name": "User roles",
    "version": "15.0.0.1.0",
    "category": "Tools",
    "author": "ABF OSIELL, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "maintainers": ["sebalix", "jcdrubay", "novawish"],
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "data/ir_module_category.xml",
        "views/role.xml",
        "views/user.xml",
        "views/group.xml",
    ],
    "installable": True,
}
