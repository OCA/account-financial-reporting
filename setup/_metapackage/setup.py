import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-account-financial-reporting",
    description="Meta package for oca-account-financial-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_financial_report',
        'odoo11-addon-account_financial_report_date_range',
        'odoo11-addon-account_tax_balance',
        'odoo11-addon-customer_activity_statement',
        'odoo11-addon-customer_outstanding_statement',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
