# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'QWeb Financial Reports',
    'version': '9.0.0.1.0',
    'category': 'Reporting',
    'summary': 'OCA Financial Reports',
    'author': 'Camptocamp SA,'
              'initOS GmbH,'
              'redCOR AG,'
              'Odoo Community Association (OCA)',
    "website": "https://odoo-community.org/",
    'depends': [
        'account',
        'account_full_reconcile',
        'date_range',
        'account_fiscal_year',
        'report_xlsx',
    ],
    'data': [
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/general_ledger_wizard_view.xml',
        'wizard/open_invoice_wizard_view.xml',
        'wizard/balance_common_wizard_view.xml',
        'wizard/partner_balance_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'wizard/balance_sheet_wizard_view.xml',
        'menuitems.xml',
        'reports.xml',
        'report/templates/aged_partner_balance.xml',
        'report/templates/general_ledger.xml',
        'report/templates/layouts.xml',
        'report/templates/open_invoice_report.xml',
        'view/account_view.xml'
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
