# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'QWeb Financial Reports',
    'version': '9.0.0.1.0',
    'category': 'Reporting',
    'summary': """
        OCA Financial Reports
    """,
    'author': 'Camptocamp SA,'
              'initOS GmbH,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.camptocamp.com',
    'depends': [
        'account',
        # 'date_range',
    ],
    'data': [
        'wizard/aged_partner_balance_wizard_view.xml',
        'wizard/ledger_report_wizard_view.xml',
        'report_menus.xml',
        'wizard/balance_common_wizard_view.xml',
        'views/report_menus.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
