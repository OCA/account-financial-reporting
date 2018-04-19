import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-account-financial-reporting",
    description="Meta package for oca-account-financial-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-account_financial_report_horizontal',
        'odoo9-addon-account_financial_report_qweb',
        'odoo9-addon-account_journal_report',
        'odoo9-addon-account_tax_balance',
        'odoo9-addon-customer_activity_statement',
        'odoo9-addon-customer_outstanding_statement',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
