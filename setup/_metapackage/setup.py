import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-account-financial-reporting",
    description="Meta package for oca-account-financial-reporting Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-account_chart_report',
        'odoo8-addon-account_export_csv',
        'odoo8-addon-account_financial_report_horizontal',
        'odoo8-addon-account_financial_report_webkit',
        'odoo8-addon-account_financial_report_webkit_xls',
        'odoo8-addon-account_journal_report_xls',
        'odoo8-addon-account_move_line_report_xls',
        'odoo8-addon-account_tax_report_no_zeroes',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
