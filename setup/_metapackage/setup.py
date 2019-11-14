import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-account-financial-reporting",
    description="Meta package for oca-account-financial-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_export_csv',
        'odoo12-addon-account_financial_report',
        'odoo12-addon-account_tax_balance',
        'odoo12-addon-mis_builder_cash_flow',
        'odoo12-addon-partner_statement',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
