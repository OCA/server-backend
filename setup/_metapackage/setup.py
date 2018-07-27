import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-base_external_dbsource',
        'odoo11-addon-base_external_dbsource_mysql',
        'odoo11-addon-base_external_dbsource_sqlite',
        'odoo11-addon-base_external_system',
        'odoo11-addon-base_suspend_security',
        'odoo11-addon-base_user_role',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
