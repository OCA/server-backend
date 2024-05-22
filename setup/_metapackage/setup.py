import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_external_dbsource>=16.0dev,<16.1dev',
        'odoo-addon-base_external_dbsource_mssql>=16.0dev,<16.1dev',
        'odoo-addon-base_external_dbsource_mysql>=16.0dev,<16.1dev',
        'odoo-addon-base_external_dbsource_sqlite>=16.0dev,<16.1dev',
        'odoo-addon-base_external_system>=16.0dev,<16.1dev',
        'odoo-addon-base_global_discount>=16.0dev,<16.1dev',
        'odoo-addon-base_group_backend>=16.0dev,<16.1dev',
        'odoo-addon-base_import_match>=16.0dev,<16.1dev',
        'odoo-addon-base_portal_type>=16.0dev,<16.1dev',
        'odoo-addon-base_user_role>=16.0dev,<16.1dev',
        'odoo-addon-base_user_role_company>=16.0dev,<16.1dev',
        'odoo-addon-base_user_role_history>=16.0dev,<16.1dev',
        'odoo-addon-server_action_navigate>=16.0dev,<16.1dev',
        'odoo-addon-server_action_sort>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
