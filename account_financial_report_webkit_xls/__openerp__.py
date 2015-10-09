# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Add XLS export to accounting reports',
    'version': '8.0.0.4.0',
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
    ],
    'test': ['tests/general_ledger.yml',
             'tests/partner_ledger.yml',
             'tests/trial_balance.yml',
             'tests/partner_balance.yml',
             'tests/open_invoices.yml'],
    'active': False,
    'installable': True,
}
