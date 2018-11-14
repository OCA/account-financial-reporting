# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Financial Report Date Range',
    'summary': """
        Add Date Range field to the Odoo OE standard addons
        financial reports wizard.
    """,
    'version': '11.0.1.0.0',
    'category': 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-financial-reporting',
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': True,
    'depends': [
        'account',
        'date_range',
    ],
    'data': [
        'wizards/accounting_report.xml',
    ],
}
