import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-base_global_discount',
        'odoo14-addon-base_import_match',
        'odoo14-addon-base_user_role',
        'odoo14-addon-base_user_role_company',
        'odoo14-addon-base_user_role_profile',
        'odoo14-addon-server_action_navigate',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
