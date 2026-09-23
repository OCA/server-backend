# Copyright 2025 gluekkanja AG <https://wwww.glueckkanja.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


{
    "name": "User roles activities",
    "summary": "Create activities to remind about user role expirations",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "author": "glueckkanja AG, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "maintainers": ["CRogos"],
    "website": "https://github.com/OCA/server-backend",
    "depends": ["base_user_role", "hr"],
    "data": [
        "data/ir_cron.xml",
        "data/mail_activity_type.xml",
        "data/config_parameter.xml",
    ],
    "installable": True,
}
