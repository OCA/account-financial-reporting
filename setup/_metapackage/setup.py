import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-account-financial-reporting",
    description="Meta package for oca-account-financial-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-account_financial_report_horizontal',
        'odoo10-addon-account_financial_report_qweb',
        'odoo10-addon-account_tax_balance',
        'odoo10-addon-customer_activity_statement',
        'odoo10-addon-customer_outstanding_statement',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
