import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-account-financial-reporting",
    description="Meta package for oca-account-financial-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_tax_balance',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
