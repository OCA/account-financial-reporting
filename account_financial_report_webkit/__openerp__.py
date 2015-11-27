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
    'description': """
Financial Reports - Webkit
==========================

This module adds or replaces the following standard OpenERP financial reports:
 - General ledger
 - Trial Balance (simple or comparative view)
 - Partner ledger
 - Partner balance
 - Open invoices report
 - Aged Partner Balance

Main improvements per report:
-----------------------------

The General ledger: details of all entries posted in your books sorted by
account.

* Filter by account is available in the wizard (no need to go to the
  Chart of Accounts to do this anymore) or by View account (the report
  will display all regular children accounts) i.e. you can select all
  P&L accounts.
* The report only prints accounts with moves OR with a non
  null balance. No more endless report with empty accounts (field:
  display account is hidden)
* initial balance computation on the fly if no open entry posted
* Thanks to a new checkbox in the account form, you will have the
  possibility to centralize any account you like.  This means you do
  not want to see all entries posted under the account ‘VAT on sales’;
  you will only see aggregated amounts by periods.
* Counterpart account is displayed for each transaction (3 accounts max.)
  to ease searching.
* Better ergonomy on the wizard: important information is displayed in
  the top part, filters are in the middle, and options are in the
  bottom or on a separate tab. There is more specific filtering on
  separate tabs. No more unique wizard layout for all financial
  reports (we have removed the journal tab for the GL report)
* improved report style

The partner ledger: details of entries relative to payable &
receivable accounts posted in your books sorted by account and
partner.

* Filter by partner now available
* Now you can see Accounts then Partner with subtotals for each
  account allowing you to check you data with trial balance and
  partner balance for instance. Accounts are ordered in the same way as
  in the Chart of account
* Period have been added (date only is not filled in since date can be
  outside period)
* Reconciliation code added
* Subtotal by account
* Alphabetical sorting (same as in partner balance)

Open invoice report : other version of the partner ledger showing
unreconciled / partially reconciled entries.

* Possibility to print unreconciled transactions only at any date in
  the past (thanks to the new field: `last_rec_date` which computes
  the last move line reconciliation date). No more pain to get open
  invoices at the last closing date.
* no initial balance computed because the report shows open invoices
  from previous years.

The Trial balance: list of accounts with balances

* You can either see the columns: initial balance, debit, credit,
  end balance or compare balances over 4 periods of your choice
* You can select the "opening" filter to get the opening trial balance
  only
* If you create an extra virtual chart (using consolidated account) of
  accounts for your P&L and your balance sheet, you can print your
  statutory accounts (with comparison over years for instance)
* If you compare 2 periods, you will get the differences in values and
  in percent

The Partner balance: list of account with balances

* Subtotal by account and partner
* Alphabetical sorting (same as in partner balance)


Aged Partner Balance: Summary of aged open amount per partner

This report is an accounting tool helping in various tasks.
You can credit control or partner balance provisions computation for instance.

The aged balance report allows you to print balances per partner
like the trial balance but add an extra information :

* It will split balances into due amounts
  (due date not reached à the end date of the report) and overdue amounts
  Overdue data are also split by period.
* For each partner following columns will be displayed:

  * Total balance (all figures must match with same date partner balance
    report).
     This column equals the sum of all following columns)

   * Due
   * Overdue <= 30 days
   * Overdue <= 60 days
   * Overdue <= 90 days
   * Overdue <= 120 days
   * Older

Hypothesis / Contraints of aged partner balance

* Overdues columns will be by default  be based on 30 days range fix number of
  days. This can be changed by changes the RANGES constraint
* All data will be displayed in company currency
* When partial payments, the payment must appear in the same colums than the
  invoice (Except if multiple payment terms)
* Data granularity: partner (will not display figures at invoices level)
* The report aggregate data per account with sub-totals
* Initial balance must be calculated the same way that
  the partner balance / Ignoring the opening entry
  in special period (idem open invoice report)
* Only accounts with internal type payable or receivable are considered
  (idem open invoice report)
* If maturity date is null then use move line date


Limitations:
------------

In order to run properly this module makes sure you have installed the
library `wkhtmltopdf` for the pdf rendering (the library path must be
set in a System Parameter `webkit_path`).

Initial balances in these reports are based either on opening entry
posted in the opening period or computed on the fly. So make sure
that your past accounting opening entries are in an opening period.
Initials balances are not computed when using the Date filter (since a
date can be outside its logical period and the initial balance could
be different when computed by data or by initial balance for the
period). The opening period is assumed to be the Jan. 1st of the year
with an opening flag and the first period of the year must start also
on Jan 1st.

Totals for amounts in currencies are effective if the partner belongs to
an account with a secondary currency.

HTML headers and footers are deactivated for these reports because of
an issue in wkhtmltopdf
(http://code.google.com/p/wkhtmltopdf/issues/detail?id=656) Instead,
the header and footer are created as text with arguments passed to
wkhtmltopdf. The texts are defined inside the report classes.
""",
    'version': '8.0.1.1.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
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
             'wizard/aged_partner_balance_wizard.xml',
             'wizard/print_journal_view.xml',
             'report_menus.xml',
             ],
    # tests order matter
    'test': ['tests/general_ledger.yml',
             'tests/partner_ledger.yml',
             'tests/trial_balance.yml',
             'tests/partner_balance.yml',
             'tests/open_invoices.yml',
             'tests/aged_trial_balance.yml'],
    # 'tests/account_move_line.yml'
    'active': False,
    'installable': True,
    'application': True,
}
