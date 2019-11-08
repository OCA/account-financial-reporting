# Copyright 2009-2018 Noviat.
# Copyright 2020 initOS GmbH <https://initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Line XLSX export',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'initOS GmbH, Noviat, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-reporting',
    'category': 'Accounting & Finance',
    'summary': 'Journal Items Excel export',
    'depends': ['account_invoicing', 'report_xlsx_helper'],
    'data': [
        'report/report_account_move_line_xlsx.xml',
    ],
    'installable': True,
}
