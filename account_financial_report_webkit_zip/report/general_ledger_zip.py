# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Matthieu Dietrich
#    Copyright Camptocamp SA 2014
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
from operator import itemgetter
from itertools import groupby
from datetime import datetime

from openerp.report import report_sxw
from openerp import pooler
from openerp.tools.translate import _
from openerp.addons.account_financial_report_webkit.report.general_ledger import GeneralLedgerWebkit
from .webkit_parser_multiple_files import MultipleFilesWebKitParser


class GeneralLedgerWebkitZip(GeneralLedgerWebkit):

    def get_account_ids(self, cursor, uid, ids, data, context=None):
        # Retrieve all ids for ZIP report
        new_ids = data['form']['account_ids'] or \
            data['form']['chart_account_id']
        return self.get_all_accounts(new_ids, exclude_type=['view'])

    def _create_empty_account(self, account_id):
        # Returns "empty" browse account (no ledger lines)
        empty_account = self.pool.get('account.account').browse(
            self.cursor, self.uid, account_id
        )
        empty_account.ledger_lines = []
        empty_account.init_balance = {}
        return empty_account

    def _split_account(self, account):
        # method to split the account according to the number of ledger lines.
        # Here are the rules for the split:
        # - first file gets the initial balance
        # - every 20000 ledger lines, open a new object

        accounts = []
        cumulated_balance = {
            'name': account.code + " - " + account.name,
            'total_debit': 0.0,
            'total_credit': 0.0,
            'cumul_balance': 0.0,
            'cumul_balance_curr': 0.0,
            'currency_name': account.currency_id.name or '',
        }
        current_account = self._create_empty_account(account.id)
        if account.init_balance and \
                (account.init_balance.get('debit', 0.0) != 0.0 or
                 account.init_balance.get('credit', 0.0) != 0.0):
            current_account.init_balance = account.init_balance

            # Add to cumulated balance
            cumulated_balance['total_debit'] += \
                account.init_balance.get('debit', 0.0)
            cumulated_balance['total_credit'] += \
                account.init_balance.get('credit', 0.0)
            cumulated_balance['cumul_balance'] += \
                account.init_balance.get('init_balance', 0.0)
            cumulated_balance['cumul_balance_curr'] += \
                account.init_balance.get('init_balance_currency', 0.0)
        ledger_lines = account.ledger_lines
        count = 1

        # Add to cumulated balance
        cumulated_balance['total_debit'] += \
            sum(line.get('debit', 0.0) for line in ledger_lines)
        cumulated_balance['total_credit'] += \
            sum(line.get('credit', 0.0) for line in ledger_lines)
        cumulated_balance['cumul_balance'] += \
            sum(line.get('balance', 0.0) for line in ledger_lines)
        cumulated_balance['cumul_balance_curr'] += \
            sum(line.get('amount_currency', 0.0) for line in ledger_lines)

        while len(ledger_lines) > 0:
            current_account.ledger_lines = ledger_lines[:20000]
            ledger_lines = ledger_lines[20000:]
            account_name = account.code + " - " + \
                account.name.replace('/', '-')
            file_name = account_name + "/" + \
                account_name + " - " + str(count) + ".pdf"
            current_account.file_name = file_name
            # Add account to objects
            accounts.append(current_account)
            current_account = self._create_empty_account(account.id)
            count += 1

        # Append first account if init balance
        if len(accounts) == 0 and account.init_balance:
            account_name = account.code + " - " + \
                account.name.replace('/', '-')
            file_name = account_name + "/" + \
                account_name + " - " + str(count) + ".pdf"
            current_account.file_name = file_name
            # Add account to objects
            accounts.append(current_account)

        return accounts, cumulated_balance

    def set_context(self, objects, data, ids, report_type=None):
        """
        Redefined from account_financial_report_webkit.
        Populate a ledger_lines and file_name attribute on browse record
        that will be used by mako template. To improve performance, we
        only call this function with one account (the search was done in
        the WebKit parser)
        """

        # Account initial balance memoizer
        init_balance_memoizer = {}

        # Reading form
        main_filter = self._get_form_param('filter', data, default='filter_no')
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        do_centralize = self._get_form_param('centralize', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)
        chart_account = self._get_chart_account_id_br(data)

        if main_filter == 'filter_no':
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)

        # computation of ledger lines
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period

        initial_balance = self.is_initial_balance_enabled(main_filter)
        initial_balance_mode = initial_balance and \
            self._get_initial_balance_mode(start) or False

        # Retrieving accounts
        if initial_balance_mode == 'initial_balance':
            init_balance_memoizer = self._compute_initial_balances(
                ids, start, fiscalyear
            )
        elif initial_balance_mode == 'opening_balance':
            init_balance_memoizer = self._read_opening_balance(ids, start)

        ledger_lines_memoizer = self._compute_account_ledger_lines(
            ids, init_balance_memoizer, main_filter, target_move, start, stop
        )
        account = self.pool.get('account.account').browse(self.cursor,
                                                          self.uid,
                                                          ids[0])
        if do_centralize and account.centralized and \
           ledger_lines_memoizer.get(account.id):
            account.ledger_lines = self._centralize_lines(
                main_filter, ledger_lines_memoizer.get(account.id, [])
            )
        else:
            account.ledger_lines = ledger_lines_memoizer.get(
                account.id, []
            )
        account.init_balance = init_balance_memoizer.get(account.id, {})

        # Split account into multiple objects (to avoid a massive file)
        objects, cumulated_balance = self._split_account(account)

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'initial_balance_mode': initial_balance_mode,
            'cumulated_balance': cumulated_balance,
        })

        # We call the super method of GeneralLedgerWebkit, to avoid
        # retrieving all lines in GeneralLedgerWebkit
        return super(GeneralLedgerWebkit, self).set_context(
            objects, data, ids, report_type=report_type
        )


MultipleFilesWebKitParser('report.account.account_report_general_ledger_zip',
                          'account.account',
                          parser=GeneralLedgerWebkitZip)
