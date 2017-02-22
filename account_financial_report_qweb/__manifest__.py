# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'QWeb Financial Reports',
    'version': '10.0.1.0.1',
    'category': 'Reporting',
    'summary': 'OCA Financial Reports',
    'author': 'Camptocamp SA,'
              'initOS GmbH,'
              'redCOR AG,'
              'Odoo Community Association (OCA)',
    "website": "https://odoo-community.org/",
    'depends': [
        'account',
        'date_range',
        'account_fiscal_year',
        'report_xlsx',
        'report',
    ],
    'data': [
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/general_ledger_wizard_view.xml',
        'wizard/open_items_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'menuitems.xml',
        'reports.xml',
        'report/templates/aged_partner_balance.xml',
        'report/templates/general_ledger.xml',
        'report/templates/layouts.xml',
        'report/templates/open_items.xml',
        'report/templates/trial_balance.xml',
        'view/account_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
