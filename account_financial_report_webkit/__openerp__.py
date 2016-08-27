# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Nicolas Bessi, Guewen Baconnier
#    Copyright Camptocamp SA 2011
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
    'name': 'Financial Reports - Webkit',
    'version': '8.0.1.2.0',
    'author': (
        "Camptocamp,"
        "Savoir-faire Linux,"
        "Odoo Community Association (OCA)"
    ),
    'license': 'AGPL-3',
    'category': 'Finance',
    'website': 'http://www.camptocamp.com',
    'images': [
        'images/ledger.png', ],
    'depends': ['account',
                'report_webkit'],
    'demo': [],
    'data': ['account_view.xml',
             'data/financial_webkit_header.xml',
             'report/report.xml',
             'wizard/wizard.xml',
             'wizard/balance_common_view.xml',
             'wizard/general_ledger_wizard_view.xml',
             'wizard/partners_ledger_wizard_view.xml',
             'wizard/trial_balance_wizard_view.xml',
             'wizard/partner_balance_wizard_view.xml',
             'wizard/open_invoices_wizard_view.xml',
             'wizard/aged_open_invoices_wizard.xml',
             'wizard/aged_partner_balance_wizard.xml',
             'wizard/print_journal_view.xml',
             'report_menus.xml',
             ],
    # tests order matter
    'test': ['test/general_ledger.yml',
             'test/partner_ledger.yml',
             'test/trial_balance.yml',
             'test/partner_balance.yml',
             'test/open_invoices.yml',
             'test/aged_trial_balance.yml'],
    # 'tests/account_move_line.yml'
    'active': False,
    'installable': True,
    'application': True,
}
