# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
#    SQL inspired from OpenERP original code
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

from operator import add

from .common_reports import CommonReportHeaderWebkit
from openerp import tools


class CommonBalanceReportHeaderWebkit(CommonReportHeaderWebkit):

    """Define common helper for balance (trial balance, P&L, BS oriented
       financial report"""

    def _get_numbers_display(self, data):
        return self._get_form_param('numbers_display', data)

    @staticmethod
    def find_key_by_value_in_list(dic, value):
        return [key for key, val in dic.iteritems() if value in val][0]

    def _get_account_details(self, account_ids, target_move, fiscalyear,
                             main_filter, start, stop, initial_balance_mode,
                             context=None):
        """
        Get details of accounts to display on the report
        @param account_ids: ids of accounts to get details
        @param target_move: selection filter for moves (all or posted)
        @param fiscalyear: browse of the fiscalyear
        @param main_filter: selection filter period / date or none
        @param start: start date or start period browse instance
        @param stop: stop date or stop period browse instance
        @param initial_balance_mode: False: no calculation,
               'opening_balance': from the opening period,
               'initial_balance': computed from previous year / periods
        @return: dict of list containing accounts details, keys are
                 the account ids
        """
        if context is None:
            context = {}

        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        use_period_ids = main_filter in (
            'filter_no', 'filter_period', 'filter_opening')

        if use_period_ids:
            if main_filter == 'filter_opening':
                period_ids = [start.id]
            else:
                period_ids = period_obj.build_ctx_periods(
                    self.cursor, self.uid, start.id, stop.id)
                # never include the opening in the debit / credit amounts
                period_ids = self.exclude_opening_periods(period_ids)

        init_balance = False
        if initial_balance_mode == 'opening_balance':
            init_balance = self._read_opening_balance(account_ids, start)
        elif initial_balance_mode:
            init_balance = self._compute_initial_balances(
                account_ids, start, fiscalyear)

        ctx = context.copy()
        ctx.update({'state': target_move,
                    'all_fiscalyear': True})

        if use_period_ids:
            ctx.update({'periods': period_ids})
        elif main_filter == 'filter_date':
            ctx.update({'date_from': start,
                        'date_to': stop})

        # in tests (when installing and testing at the same time),
        # the read below might fail because it relies on the order
        # given by parent_store
        if tools.config['test_enable']:
            account_obj._parent_store_compute(self.cursor)

        accounts = account_obj.read(
            self.cursor,
            self.uid,
            account_ids,
            ['type', 'code', 'name', 'debit', 'credit',
                'balance', 'parent_id', 'level', 'child_id'],
            context=ctx)

        accounts_by_id = {}
        for account in accounts:
            if init_balance:
                # sum for top level views accounts
                child_ids = account_obj._get_children_and_consol(
                    self.cursor, self.uid, account['id'], ctx)
                if child_ids:
                    child_init_balances = [
                        init_bal['init_balance']
                        for acnt_id, init_bal in init_balance.iteritems()
                        if acnt_id in child_ids]
                    top_init_balance = reduce(add, child_init_balances)
                    account['init_balance'] = top_init_balance
                else:
                    account.update(init_balance[account['id']])
                account['balance'] = account['init_balance'] + \
                    account['debit'] - account['credit']
            accounts_by_id[account['id']] = account
        return accounts_by_id

    def _get_comparison_details(self, data, account_ids, target_move,
                                comparison_filter, index, context=None):
        """

        @param data: data of the wizard form
        @param account_ids: ids of the accounts to get details
        @param comparison_filter: selected filter on the form for
               the comparison (filter_no, filter_year, filter_period,
                               filter_date)
        @param index: index of the fields to get
                (ie. comp1_fiscalyear_id where 1 is the index)
        @return: dict of account details (key = account id)
        """
        fiscalyear = self._get_info(
            data, "comp%s_fiscalyear_id" % (index,), 'account.fiscalyear')
        start_period = self._get_info(
            data, "comp%s_period_from" % (index,), 'account.period')
        stop_period = self._get_info(
            data, "comp%s_period_to" % (index,), 'account.period')
        start_date = self._get_form_param("comp%s_date_from" % (index,), data)
        stop_date = self._get_form_param("comp%s_date_to" % (index,), data)
        init_balance = self.is_initial_balance_enabled(comparison_filter)

        accounts_by_ids = {}
        comp_params = {}
        details_filter = comparison_filter
        if comparison_filter != 'filter_no':
            start_period, stop_period, start, stop = \
                self._get_start_stop_for_filter(
                    comparison_filter, fiscalyear, start_date, stop_date,
                    start_period, stop_period)
            if comparison_filter == 'filter_year':
                details_filter = 'filter_no'

            initial_balance_mode = init_balance \
                and self._get_initial_balance_mode(start) or False
            accounts_by_ids = self._get_account_details(
                account_ids, target_move, fiscalyear, details_filter,
                start, stop, initial_balance_mode, context=context)
            comp_params = {
                'comparison_filter': comparison_filter,
                'fiscalyear': fiscalyear,
                'start': start,
                'stop': stop,
                'initial_balance': init_balance,
                'initial_balance_mode': initial_balance_mode,
            }

        return accounts_by_ids, comp_params

    def _get_diff(self, balance, previous_balance):
        """
        @param balance: current balance
        @param previous_balance: last balance
        @return: dict of form {'diff': difference,
                               'percent_diff': diff in percentage}
        """
        diff = balance - previous_balance

        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(
            self.cursor, self.uid, 'Account')
        # round previous balance with account precision to avoid big numbers
        # if previous balance is 0.0000001 or a any very small number
        if round(previous_balance, precision) == 0:
            percent_diff = False
        else:
            percent_diff = round(diff / previous_balance * 100, precision)

        return {'diff': diff, 'percent_diff': percent_diff}

    def _comp_filters(self, data, comparison_number):
        """
        @param data: data of the report
        @param comparison_number: number of comparisons
        @return: list of comparison filters, nb of comparisons used and
                 comparison mode (no_comparison, single, multiple)
        """
        comp_filters = []
        for index in range(comparison_number):
            comp_filters.append(
                self._get_form_param("comp%s_filter" % (index,), data,
                                     default='filter_no'))

        nb_comparisons = len(
            [comp_filter for comp_filter in comp_filters
                if comp_filter != 'filter_no'])
        if not nb_comparisons:
            comparison_mode = 'no_comparison'
        elif nb_comparisons > 1:
            comparison_mode = 'multiple'
        else:
            comparison_mode = 'single'
        return comp_filters, nb_comparisons, comparison_mode

    def _get_start_stop_for_filter(self, main_filter, fiscalyear, start_date,
                                   stop_date, start_period, stop_period):
        if main_filter in ('filter_no', 'filter_year'):
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)
        elif main_filter == 'filter_opening':
            opening_period = self._get_st_fiscalyear_period(
                fiscalyear, special=True)
            start_period = stop_period = opening_period
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period

        return start_period, stop_period, start, stop

    def compute_balance_data(self, data, filter_report_type=None):
        lang = self.localcontext.get('lang')
        lang_ctx = lang and {'lang': lang} or {}
        new_ids = (data['form']['account_ids'] or
                   [data['form']['chart_account_id']])
        max_comparison = self._get_form_param(
            'max_comparison', data, default=0)
        main_filter = self._get_form_param('filter', data, default='filter_no')

        comp_filters, nb_comparisons, comparison_mode = self._comp_filters(
            data, max_comparison)

        fiscalyear = self.get_fiscalyear_br(data)

        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)

        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        chart_account = self._get_chart_account_id_br(data)

        start_period, stop_period, start, stop = \
            self._get_start_stop_for_filter(main_filter, fiscalyear,
                                            start_date, stop_date,
                                            start_period, stop_period)

        init_balance = self.is_initial_balance_enabled(main_filter)
        initial_balance_mode = init_balance and self._get_initial_balance_mode(
            start) or False

        # Retrieving accounts
        ctx = {}
        if data['form'].get('account_level'):
            # Filter by account level
            ctx['account_level'] = int(data['form']['account_level'])
        account_ids = self.get_all_accounts(
            new_ids, only_type=filter_report_type, context=ctx)

        # get details for each account, total of debit / credit / balance
        accounts_by_ids = self._get_account_details(
            account_ids, target_move, fiscalyear, main_filter, start, stop,
            initial_balance_mode, context=lang_ctx)

        comparison_params = []
        comp_accounts_by_ids = []
        for index in range(max_comparison):
            if comp_filters[index] != 'filter_no':
                comparison_result, comp_params = self._get_comparison_details(
                    data, account_ids, target_move, comp_filters[index], index,
                    context=lang_ctx)
                comparison_params.append(comp_params)
                comp_accounts_by_ids.append(comparison_result)

        objects = self.pool.get('account.account').browse(self.cursor,
                                                          self.uid,
                                                          account_ids,
                                                          context=lang_ctx)

        to_display_accounts = dict.fromkeys(account_ids, True)
        init_balance_accounts = dict.fromkeys(account_ids, False)
        comparisons_accounts = dict.fromkeys(account_ids, [])
        debit_accounts = dict.fromkeys(account_ids, False)
        credit_accounts = dict.fromkeys(account_ids, False)
        balance_accounts = dict.fromkeys(account_ids, False)

        for account in objects:
            if account.type == 'consolidation':
                to_display_accounts.update(
                    dict([(a.id, False) for a in account.child_consol_ids]))
            elif account.type == 'view':
                to_display_accounts.update(
                    dict([(a.id, True) for a in account.child_id]))
            debit_accounts[account.id] = \
                accounts_by_ids[account.id]['debit']
            credit_accounts[account.id] = \
                accounts_by_ids[account.id]['credit']
            balance_accounts[account.id] = \
                accounts_by_ids[account.id]['balance']
            init_balance_accounts[account.id] =  \
                accounts_by_ids[account.id].get('init_balance', 0.0)

            # if any amount is != 0 in comparisons, we have to display the
            # whole account
            display_account = False
            comp_accounts = []
            for comp_account_by_id in comp_accounts_by_ids:
                values = comp_account_by_id.get(account.id)
                values.update(
                    self._get_diff(balance_accounts[account.id],
                                   values['balance']))
                display_account = any((values.get('credit', 0.0),
                                       values.get('debit', 0.0),
                                       values.get('balance', 0.0),
                                       values.get('init_balance', 0.0)))
                comp_accounts.append(values)
            comparisons_accounts[account.id] = comp_accounts
            # we have to display the account if a comparison as an amount or
            # if we have an amount in the main column
            # we set it as a property to let the data in the report if someone
            # want to use it in a custom report
            display_account = display_account\
                or any((debit_accounts[account.id],
                        credit_accounts[account.id],
                        balance_accounts[account.id],
                        init_balance_accounts[account.id]))
            to_display_accounts.update(
                {account.id: display_account and
                 to_display_accounts[account.id]})

        context_report_values = {
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'comparison_mode': comparison_mode,
            'nb_comparison': nb_comparisons,
            'initial_balance': init_balance,
            'initial_balance_mode': initial_balance_mode,
            'comp_params': comparison_params,
            'to_display_accounts': to_display_accounts,
            'init_balance_accounts': init_balance_accounts,
            'comparisons_accounts': comparisons_accounts,
            'debit_accounts': debit_accounts,
            'credit_accounts': credit_accounts,
            'balance_accounts': balance_accounts,
        }

        return objects, new_ids, context_report_values
