import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-base_external_dbsource',
        'odoo13-addon-base_external_dbsource_mssql',
        'odoo13-addon-base_external_dbsource_mysql',
        'odoo13-addon-base_external_dbsource_sqlite',
        'odoo13-addon-base_external_system',
        'odoo13-addon-base_global_discount',
        'odoo13-addon-base_import_match',
        'odoo13-addon-base_user_role',
        'odoo13-addon-base_user_role_history',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
