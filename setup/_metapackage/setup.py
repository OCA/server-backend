import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-base_external_dbsource',
        'odoo12-addon-base_external_dbsource_mssql',
        'odoo12-addon-base_external_dbsource_mysql',
        'odoo12-addon-base_external_dbsource_sqlite',
        'odoo12-addon-base_external_system',
        'odoo12-addon-base_global_discount',
        'odoo12-addon-base_import_match',
        'odoo12-addon-base_suspend_security',
        'odoo12-addon-base_user_role',
        'odoo12-addon-base_user_role_history',
        'odoo12-addon-base_user_role_profile',
        'odoo12-addon-base_user_role_profile_example',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
