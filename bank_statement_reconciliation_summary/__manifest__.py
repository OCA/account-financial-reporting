# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Bank Statement Reconciliation Summary',
    'category': 'Account',
    'summary': 'Bank Statement Reconciliation Summary',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Eficent, '
              'Serpent Consulting Services Pvt. Ltd.,'
              'Odoo Community Association (OCA)',
    'depends': ['account', 'account_financial_report_qweb'],
    'data': [
        'report/summary_report.xml',
        'report/report.xml',
        'wizard/bank_statement_reconciliation_summary_wizard_view.xml',
    ],
    'installable': True,
}
