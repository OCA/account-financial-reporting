# -*- coding: utf-8 -*-
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

from collections import defaultdict
from operator import add

from openerp.tools.float_utils import float_is_zero

from .common_balance_reports import CommonBalanceReportHeaderWebkit
from .common_partner_reports import CommonPartnersReportHeaderWebkit


class CommonPartnerBalanceReportHeaderWebkit(CommonBalanceReportHeaderWebkit,
                                             CommonPartnersReportHeaderWebkit):

    """Define common helper for balance (trial balance, P&L,
        BS oriented financial report"""

    def _get_account_partners_details(self, account_by_ids, main_filter,
                                      target_move, start, stop,
                                      initial_balance_mode,
                                      partner_filter_ids=False,
                                      display_partner='all'):
        res = {}
        filter_from = False
        if main_filter in ('filter_period', 'filter_no', 'filter_opening'):
            filter_from = 'period'
        elif main_filter == 'filter_date':
            filter_from = 'date'

        partners_init_balances_by_ids = {}
        for account_id, account_details in account_by_ids.iteritems():
            partners_init_balances_by_ids.update(
                self._get_partners_initial_balances(
                    account_id, start, initial_balance_mode,
                    partner_filter_ids=partner_filter_ids,
                    # we'll never exclude reconciled entries in the legal
                    # reports
                    exclude_reconcile=False))
            opening_mode = 'exclude_opening'
            if main_filter == 'filter_opening':
                opening_mode = 'include_opening'
            # get credit and debit for partner
            details = self._get_partners_totals_account(
                filter_from,
                account_id,
                start,
                stop,
                target_move,
                partner_filter_ids=partner_filter_ids,
                mode=opening_mode)

            # merge initial balances in partner details
            if partners_init_balances_by_ids.get(account_id):
                for partner_id, initial_balances in \
                        partners_init_balances_by_ids[account_id].iteritems():
                    if initial_balances.get('init_balance'):
                        details[partner_id].update(
                            {'init_balance': initial_balances['init_balance']})

            # compute balance for the partner
            for partner_id, partner_details in details.iteritems():
                details[partner_id]['balance'] = details[partner_id].\
                    get('init_balance', 0.0) + \
                    details[partner_id].get('debit', 0.0) - \
                    details[partner_id].get('credit', 0.0)

            if display_partner == 'non-zero_balance':
                details = {
                    k: v
                    for k, v in details.iteritems()
                    if not float_is_zero(v['balance'], precision_digits=5)
                }
            res[account_id] = details

        return res

    def _get_partners_initial_balances(self, account_ids, start_period,
                                       initial_balance_mode,
                                       partner_filter_ids=None,
                                       exclude_reconcile=False):
        # we get the initial balance from the opening period (opening_balance)
        # when the opening period is included in the start period and
        # when there is at least one entry in the opening period. Otherwise we
        # compute it from previous periods
        if initial_balance_mode == 'opening_balance':
            opening_period_selected = self.get_included_opening_period(
                start_period)
            res = self._compute_partners_initial_balances(
                account_ids, start_period, partner_filter_ids,
                force_period_ids=opening_period_selected,
                exclude_reconcile=exclude_reconcile)
        elif initial_balance_mode == 'initial_balance':
            res = self._compute_partners_initial_balances(
                account_ids, start_period, partner_filter_ids,
                exclude_reconcile=exclude_reconcile)
        else:
            res = {}
        return res

    def _get_partners_totals_account(self, filter_from, account_id, start,
                                     stop, target_move,
                                     partner_filter_ids=None,
                                     mode='exclude_opening'):
        final_res = defaultdict(dict)

        sql_select = """
                 SELECT account_move_line.partner_id,
                        sum(account_move_line.debit) AS debit,
                        sum(account_move_line.credit) AS credit
                 FROM account_move_line"""
        sql_joins = ''
        sql_where = "WHERE account_move_line.account_id = %(account_id)s \
                     AND account_move_line.state = 'valid' "
        method = getattr(self, '_get_query_params_from_' + filter_from + 's')
        sql_conditions, search_params = method(start, stop, mode=mode)
        sql_where += sql_conditions

        if partner_filter_ids:
            sql_where += "   AND account_move_line.partner_id \
                             in %(partner_ids)s"
            search_params.update({'partner_ids': tuple(partner_filter_ids)})

        if target_move == 'posted':
            sql_joins += "INNER JOIN account_move \
                            ON account_move_line.move_id = account_move.id"
            sql_where += " AND account_move.state = %(target_move)s"
            search_params.update({'target_move': target_move})

        sql_groupby = "GROUP BY account_move_line.partner_id"

        search_params.update({'account_id': account_id})
        query = ' '.join((sql_select, sql_joins, sql_where, sql_groupby))

        self.cursor.execute(query, search_params)
        res = self.cursor.dictfetchall()
        if res:
            for row in res:
                final_res[row['partner_id']] = row
        return final_res

    def _get_filter_type(self, result_selection):
        filter_type = ('payable', 'receivable')
        if result_selection == 'customer':
            filter_type = ('receivable',)
        if result_selection == 'supplier':
            filter_type = ('payable',)
        return filter_type

    def _get_partners_comparison_details(self, data, account_ids, target_move,
                                         comparison_filter, index,
                                         partner_filter_ids=False):
        """

        @param data: data of the wizard form
        @param account_ids: ids of the accounts to get details
        @param comparison_filter: selected filter on the form for
            the comparison (filter_no, filter_year, filter_period, filter_date)
        @param index: index of the fields to get (ie. comp1_fiscalyear_id
            where 1 is the index)
        @param partner_filter_ids: list of ids of partners to select
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

        comp_params = {}
        accounts_details_by_ids = defaultdict(dict)
        if comparison_filter != 'filter_no':
            start_period, stop_period, start, stop = \
                self._get_start_stop_for_filter(
                    comparison_filter, fiscalyear, start_date, stop_date,
                    start_period, stop_period)
            details_filter = comparison_filter
            if comparison_filter == 'filter_year':
                details_filter = 'filter_no'

            initial_balance_mode = init_balance \
                and self._get_initial_balance_mode(start) or False

            accounts_by_ids = self._get_account_details(
                account_ids, target_move, fiscalyear, details_filter, start,
                stop, initial_balance_mode)

            partner_details_by_ids = self._get_account_partners_details(
                accounts_by_ids, details_filter,
                target_move, start, stop, initial_balance_mode,
                partner_filter_ids=partner_filter_ids,
                display_partner=data['form']['display_partner']
            )

            for account_id in account_ids:
                accounts_details_by_ids[account_id][
                    'account'] = accounts_by_ids[account_id]
                accounts_details_by_ids[account_id][
                    'partners_amounts'] = partner_details_by_ids[account_id]

            comp_params = {
                'comparison_filter': comparison_filter,
                'fiscalyear': fiscalyear,
                'start': start,
                'stop': stop,
                'initial_balance_mode': initial_balance_mode,
            }

        return accounts_details_by_ids, comp_params

    def compute_partner_balance_data(self, data, filter_report_type=None):
        lang = self.localcontext.get('lang')
        lang_ctx = lang and {'lang': lang} or {}
        new_ids = data['form']['account_ids'] or data[
            'form']['chart_account_id']
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
        result_selection = self._get_form_param('result_selection', data)
        partner_ids = self._get_form_param('partner_ids', data)

        filter_type = self._get_filter_type(result_selection)

        start_period, stop_period, start, stop = \
            self._get_start_stop_for_filter(
                main_filter, fiscalyear, start_date, stop_date, start_period,
                stop_period)

        initial_balance = self.is_initial_balance_enabled(main_filter)
        initial_balance_mode = initial_balance \
            and self._get_initial_balance_mode(start) or False

        # Retrieving accounts
        account_ids = self.get_all_accounts(
            new_ids, only_type=filter_type,
            filter_report_type=filter_report_type)

        # get details for each accounts, total of debit / credit / balance
        accounts_by_ids = self._get_account_details(
            account_ids, target_move, fiscalyear, main_filter, start, stop,
            initial_balance_mode, context=lang_ctx)

        partner_details_by_ids = self._get_account_partners_details(
            accounts_by_ids, main_filter, target_move, start, stop,
            initial_balance_mode, partner_filter_ids=partner_ids,
            display_partner=data['form']['display_partner'])

        comparison_params = []
        comp_accounts_by_ids = []
        for index in range(max_comparison):
            if comp_filters[index] != 'filter_no':
                comparison_result, comp_params = self.\
                    _get_partners_comparison_details(
                        data, account_ids,
                        target_move,
                        comp_filters[index],
                        index,
                        partner_filter_ids=partner_ids)
                comparison_params.append(comp_params)
                comp_accounts_by_ids.append(comparison_result)
        objects = self.pool.get('account.account').browse(self.cursor,
                                                          self.uid,
                                                          account_ids,
                                                          context=lang_ctx)

        init_balance_accounts = {}
        comparisons_accounts = {}
        partners_order_accounts = {}
        partners_amounts_accounts = {}
        debit_accounts = {}
        credit_accounts = {}
        balance_accounts = {}

        for account in objects:
            if not account.parent_id:  # hide top level account
                continue
            debit_accounts[account.id] = accounts_by_ids[account.id]['debit']
            credit_accounts[account.id] = accounts_by_ids[account.id]['credit']
            balance_accounts[account.id] = \
                accounts_by_ids[account.id]['balance']
            init_balance_accounts[account.id] = accounts_by_ids[
                account.id].get('init_balance', 0.0)
            partners_amounts_accounts[account.id] =\
                partner_details_by_ids[account.id]
            comp_accounts = []
            for comp_account_by_id in comp_accounts_by_ids:
                values = comp_account_by_id.get(account.id)

                values['account'].update(
                    self._get_diff(balance_accounts[account.id],
                                   values['account'].get('balance', 0.0)))
                comp_accounts.append(values)

                for partner_id, partner_values in \
                        values['partners_amounts'].copy().iteritems():
                    partners_amounts_account =\
                        partners_amounts_accounts[account.id]
                    base_partner_balance =\
                        partners_amounts_account[partner_id]['balance']\
                        if partners_amounts_accounts.get(account.id)\
                        and partners_amounts_accounts.get(account.id)\
                        .get(partner_id) else 0.0
                    partner_values.update(self._get_diff(
                        base_partner_balance,
                        partner_values.get('balance', 0.0)))
                    values['partners_amounts'][
                        partner_id].update(partner_values)

            comparisons_accounts[account.id] = comp_accounts

            all_partner_ids = reduce(add, [comp['partners_amounts'].keys()
                                           for comp in comp_accounts],
                                     partners_amounts_accounts[account.id]
                                     .keys())

            partners_order_accounts[account.id] = \
                self._order_partners(all_partner_ids)

        context_report_values = {
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'comparison_mode': comparison_mode,
            'nb_comparison': nb_comparisons,
            'comp_params': comparison_params,
            'initial_balance_mode': initial_balance_mode,
            'compute_diff': self._get_diff,
            'init_balance_accounts': init_balance_accounts,
            'comparisons_accounts': comparisons_accounts,
            'partners_order_accounts': partners_order_accounts,
            'partners_amounts_accounts': partners_amounts_accounts,
            'debit_accounts': debit_accounts,
            'credit_accounts': credit_accounts,
            'balance_accounts': balance_accounts,
        }

        return objects, new_ids, context_report_values
