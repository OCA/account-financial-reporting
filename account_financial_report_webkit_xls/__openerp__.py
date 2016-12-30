# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Add XLS export to accounting reports',
    'version': '8.0.0.5.0',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'description': """

    This module adds XLS export to the following accounting reports:
        - general ledger
        - trial balance
        - partner ledger
        - partner balance
        - open invoices

    """,
    'depends': ['report_xls', 'account_financial_report_webkit'],
    'demo': [],
    'data': [
        'wizard/general_ledger_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'wizard/partners_ledger_wizard_view.xml',
        'wizard/partners_balance_wizard_view.xml',
        'wizard/open_invoices_wizard_view.xml',
        'wizard/aged_partner_balance_wizard.xml',
    ],
    'test': ['tests/general_ledger.yml',
             'tests/partner_ledger.yml',
             'tests/trial_balance.yml',
             'tests/partner_balance.yml',
             'tests/open_invoices.yml'],
    'active': False,
    'installable': True,
}
