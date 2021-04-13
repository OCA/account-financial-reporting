# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'QWeb Financial Reports',
    'version': '10.0.3.1.3',
    'category': 'Reporting',
    'summary': 'OCA Financial Reports',
    'author': 'Camptocamp SA,'
              'initOS GmbH,'
              'redCOR AG,'
              'ACSONE SA/NV,'
              'Odoo Community Association (OCA)',
    "website": "https://odoo-community.org/",
    'depends': [
        'account',
        'account_group',    # account-financial-tools
        'date_range',
        'report_xlsx',
        'report',
        'web_widget_many2many_tags_multi_selection',
    ],
    'data': [
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/general_ledger_wizard_view.xml',
        'wizard/journal_report_wizard.xml',
        'wizard/open_items_wizard_view.xml',
        'wizard/trial_balance_wizard_view.xml',
        'menuitems.xml',
        'reports.xml',
        'report/templates/aged_partner_balance.xml',
        'report/templates/general_ledger.xml',
        'report/templates/journal.xml',
        'report/templates/layouts.xml',
        'report/templates/open_items.xml',
        'report/templates/trial_balance.xml',
        'view/account_view.xml',
        'view/report_template.xml',
        'view/report_general_ledger.xml',
        'view/report_journal_ledger.xml',
        'view/report_trial_balance.xml',
        'view/report_open_items.xml',
        'view/report_aged_partner_balance.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
