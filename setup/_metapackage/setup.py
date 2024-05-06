import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_external_dbsource>=15.0dev,<15.1dev',
        'odoo-addon-base_external_dbsource_mssql>=15.0dev,<15.1dev',
        'odoo-addon-base_external_dbsource_mysql>=15.0dev,<15.1dev',
        'odoo-addon-base_external_dbsource_sap_hana>=15.0dev,<15.1dev',
        'odoo-addon-base_external_dbsource_sqlite>=15.0dev,<15.1dev',
        'odoo-addon-base_external_system>=15.0dev,<15.1dev',
        'odoo-addon-base_global_discount>=15.0dev,<15.1dev',
        'odoo-addon-base_ical>=15.0dev,<15.1dev',
        'odoo-addon-base_import_match>=15.0dev,<15.1dev',
        'odoo-addon-base_user_role>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
