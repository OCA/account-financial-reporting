# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Bank Reconciliation Report',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'summary': 'Adds an XLSX report to help on bank reconciliation',
    'depends': ['account', 'report_xlsx'],
    'data': [
        'report/report.xml',
        'views/account_bank_statement_view.xml',
        ],
    'installable': True,
}
