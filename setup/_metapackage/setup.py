import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-server-backend",
    description="Meta package for oca-server-backend Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-base_user_role',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
