# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Add XLS export to accounting reports',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'depends': ['report_xls', 'account_financial_report_webkit'],
    'demo': [],
    'data': [
        'wizard/general_ledger_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'wizard/partners_ledger_wizard_view.xml',
        'wizard/partners_balance_wizard_view.xml',
        'wizard/open_invoices_wizard_view.xml',
        'wizard/aged_partner_balance_wizard.xml',
        'wizard/aged_open_invoices_wizard.xml',
    ],
    'test': ['test/general_ledger.yml',
             'test/partner_ledger.yml',
             'test/trial_balance.yml',
             'test/partner_balance.yml',
             'test/open_invoices.yml'],
    'installable': True,
}
