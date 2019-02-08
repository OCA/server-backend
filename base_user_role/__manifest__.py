# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'User roles',
    'version': '12.0.1.0.0',
    'category': 'Tools',
    'author': 'ABF OSIELL, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'maintainers': ['ABF OSIELL', 'jcdrubay'],
    'website': 'https://github.com/OCA/server-backend',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/ir_module_category.xml',
        'views/role.xml',
        'views/user.xml',
    ],
    'installable': True,
}
