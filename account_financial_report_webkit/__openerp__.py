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
# TODO refactor helper in order to act more like mixin
# By using properties we will have a more simple signature in fuctions
{
    'name': 'Webkit based extended report financial report',
    'description': """
This module replace the following standard openerp financial reports :
 - General ledger
 - Trial Balance (simple or comparative view)
 - Partner ledger
 - Partner balance
 - Open invoices report


Main improvements per report:

 * The General ledger: details of all entries posted in your books sorted by account.
  - Filter by account in the wizard (no need to go to the Chart of account to do this anymore) or by view account (the report will display all regular children account) ie: you can select all P&L accounts.
  - The report will now print only account with movements OR with a balance not null. No more endless report with accounts with no data. (field: display account is hidden)
  - initial balance calculation on the fly if no open entry posted
  - Thanks to a new checkbox in account form, you will have possibility to centralize any accounts you like. ie: you do not want to see all entries posted under the account ‘VAT on sales’ ; you will only see aggregated amounts by periods.
  - Counterpart account displayed for each transaction (3 accounts max.) to ease searching.
  - Better ergonomy on the wizard: important information at the top, filters in the middle, options at the bottom or separate tab, more specific filtering on a other tabs. No more unique wizard layout for all financial reports (ie: we have removed the journal tab for the GL report)
  - improved report style

 * The partner ledger: details of entries relative to payable & receivable accounts posted in your books sorted by account and partner.
  - Filter by partner now possible
  - Now you can see accounts then Partner with subtotals for each account allowing you to check you data with trial balance and partner balance for instance & accounts are ordered the same way than in the Chart of account
  - period have been added (date only is uncompleted since date can be outside period)
  - Reconciliation code added
  - subtotal by account
  - alpha sorting (same in partner balance)

 * Open invoice report : other version of the partner ledger showing unreconciled / partially reconcies entries
(added on the 20/01/2012)
  - Possibility to print unreconciled transactions only at any date in the past (thanks to the brand-new field: last_rec_date which calculated the last move line reconciled date). No more pain to get open invoices at the last closing date.
  - no initial balance calculated because the report shows open invoices from previous years.

 * The Trial balance: list of account with balances
  - you can either see the column : Initial balance , debit, credit , end balance or compare balances over 4 periods of your choice
  - You can select the filter opening to get the opening trial balance only
  - If you create a extra virtual charts (using consolidated account) of account for your P&L and your balance sheet , you can print your statutory accounts (with comparision over years for ex.)
  - If you compare 2 periods, you will get differences in value and % also

 * The Partner balance: list of account with balances
  - subtotal by account & partner
  - alpha sorting (same in partner balance)

Limitations:
In order to run properly this module make sure you have installed the librairie ‘wkhtmltopdf’ for the pdf rendering (this library path must be added to you company settings).

Initial balances in these reports are based either on opening entry posted in the opening period or calculated on the fly. So make sure, your past accounting opening entries are in a opening period.
Initials balances are not calculated when using date filter (since a date can be outside its logical period and IB could be different by date Vs IB by period)
The opening period is assumed to be the 01.01 of the year with an opening flag and the first period of the year must starts also the 01.01

Totals for amount in currencies are affective if the partner belong to an account with a secondary currency.

html headers and footers are deactivated for these reports because of an issue of wkhtmltopdf : http://code.google.com/p/wkhtmltopdf/issues/detail?id=656
Instead, the header and footer are created as text with arguments passed to wkhtmltopdf. The texts are defined inside the report classes.

""",
    'version': '1.0',
    'author': 'Camptocamp',
    'category': 'Finance',
    'website': 'http://www.camptocamp.com',
    'images': [
        'images/ledger.png',],
    'depends': ['account',
                'report_webkit'],
    'init_xml': [],
    'demo_xml' : [],
    'update_xml': ['account_view.xml',
                   'account_move_line_view.xml',
                   'data/financial_webkit_header.xml',
                   'report/report.xml',
                   'wizard/wizard.xml',
                   'wizard/balance_common_view.xml',
                   'wizard/general_ledger_wizard_view.xml',
                   'wizard/partners_ledger_wizard_view.xml',
                   'wizard/trial_balance_wizard_view.xml',
                   'wizard/partner_balance_wizard_view.xml',
                   'wizard/open_invoices_wizard_view.xml',
                   'report_menus.xml',
#                   'wizard/profit_loss_wizard_view.xml',
                   ],
    # tests order matter
    'test': ['tests/general_ledger.yml',
             'tests/partner_ledger.yml',
             'tests/trial_balance.yml',
             'tests/partner_balance.yml',
             'tests/open_invoices.yml',],
    #'tests/account_move_line.yml'
    'active': False,
    'installable': True,
}
