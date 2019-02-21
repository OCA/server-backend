import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-base_import_match',
        'odoo12-addon-base_suspend_security',
        'odoo12-addon-base_user_role',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
