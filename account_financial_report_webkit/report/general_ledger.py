# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
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

from operator import itemgetter
from itertools import groupby
from datetime import datetime

from openerp.report import report_sxw
from openerp.modules.registry import RegistryManager
from openerp.tools.translate import _
from .common_reports import CommonReportHeaderWebkit
from .webkit_parser_header_fix import HeaderFooterTextWebKitParser


class GeneralLedgerWebkit(report_sxw.rml_parse, CommonReportHeaderWebkit):

    # pylint: disable=old-api7-method-defined
    def __init__(self, cursor, uid, name, context):
        super(GeneralLedgerWebkit, self).__init__(
            cursor, uid, name, context=context)
        self.pool = RegistryManager.get(self.cr.dbname)
        self.cursor = self.cr

        company = self.pool.get('res.users').browse(
            self.cr, uid, uid, context=context).company_id
        header_report_name = ' - '.join(
            (_('GENERAL LEDGER'), company.name, company.currency_id.name))

        footer_date_time = self.formatLang(
            str(datetime.today()), date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('General Ledger'),
            'display_account': self._get_display_account,
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'initial_balance': self._get_initial_balance,
            'amount_currency': self._get_amount_currency,
            'display_target_move': self._get_display_target_move,
            'accounts': self._get_accounts_br,
            'additional_args': [
                ('--header-font-name', 'Helvetica'),
                ('--footer-font-name', 'Helvetica'),
                ('--header-font-size', '10'),
                ('--footer-font-size', '6'),
                ('--header-left', header_report_name),
                ('--header-spacing', '2'),
                ('--footer-left', footer_date_time),
                ('--footer-right',
                 ' '.join((_('Page'), '[page]', _('of'), '[topage]'))),
                ('--footer-line',),
            ],
        })

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will be
        used by mako template"""
        lang = self.localcontext.get('lang')
        lang_ctx = lang and {'lang': lang} or {}
        new_ids = data['form']['account_ids'] or data[
            'form']['chart_account_id']

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
        initial_balance_mode = initial_balance \
            and self._get_initial_balance_mode(start) or False

        # Retrieving accounts
        accounts = self.get_all_accounts(new_ids, exclude_type=['view'])
        if initial_balance_mode == 'initial_balance':
            init_balance_memoizer = self._compute_initial_balances(
                accounts, start, fiscalyear)
        elif initial_balance_mode == 'opening_balance':
            init_balance_memoizer = self._read_opening_balance(accounts, start)

        ledger_lines_memoizer = self._compute_account_ledger_lines(
            accounts, init_balance_memoizer, main_filter, target_move, start,
            stop)
        objects = self.pool.get('account.account').browse(self.cursor,
                                                          self.uid,
                                                          accounts,
                                                          context=lang_ctx)

        init_balance = {}
        ledger_lines = {}
        for account in objects:
            if do_centralize and account.centralized \
                    and ledger_lines_memoizer.get(account.id):
                ledger_lines[account.id] = self._centralize_lines(
                    main_filter, ledger_lines_memoizer.get(account.id, []))
            else:
                ledger_lines[account.id] = ledger_lines_memoizer.get(
                    account.id, [])
            init_balance[account.id] = init_balance_memoizer.get(account.id,
                                                                 {})

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'initial_balance_mode': initial_balance_mode,
            'init_balance': init_balance,
            'ledger_lines': ledger_lines,
        })

        return super(GeneralLedgerWebkit, self).set_context(
            objects, data, new_ids, report_type=report_type)

    def _centralize_lines(self, filter, ledger_lines, context=None):
        """ Group by period in filter mode 'period' or on one line in filter
            mode 'date' ledger_lines parameter is a list of dict built
            by _get_ledger_lines"""
        def group_lines(lines):
            if not lines:
                return {}
            sums = reduce(lambda line, memo:
                          dict((key, value + memo[key]) for key, value
                               in line.iteritems() if key in
                               ('balance', 'debit', 'credit')), lines)

            res_lines = {
                'balance': sums['balance'],
                'debit': sums['debit'],
                'credit': sums['credit'],
                'lname': _('Centralized Entries'),
                'account_id': lines[0]['account_id'],
            }
            return res_lines

        centralized_lines = []
        if filter == 'filter_date':
            # by date we centralize all entries in only one line
            centralized_lines.append(group_lines(ledger_lines))

        else:  # by period
            # by period we centralize all entries in one line per period
            period_obj = self.pool.get('account.period')
            # we need to sort the lines per period in order to use groupby
            # unique ids of each used period id in lines
            period_ids = list(
                set([line['lperiod_id'] for line in ledger_lines]))
            # search on account.period in order to sort them by date_start
            sorted_period_ids = period_obj.search(
                self.cr, self.uid, [('id', 'in', period_ids)],
                order='special desc, date_start', context=context)
            sorted_ledger_lines = sorted(
                ledger_lines, key=lambda x: sorted_period_ids.
                index(x['lperiod_id']))

            for period_id, lines_per_period_iterator in groupby(
                    sorted_ledger_lines, itemgetter('lperiod_id')):
                lines_per_period = list(lines_per_period_iterator)
                if not lines_per_period:
                    continue
                group_per_period = group_lines(lines_per_period)
                group_per_period.update({
                    'lperiod_id': period_id,
                    # period code is anyway the same on each line per period
                    'period_code': lines_per_period[0]['period_code'],
                })
                centralized_lines.append(group_per_period)

        return centralized_lines

    def _compute_account_ledger_lines(self, accounts_ids,
                                      init_balance_memoizer, main_filter,
                                      target_move, start, stop):
        res = {}
        for acc_id in accounts_ids:
            move_line_ids = self.get_move_lines_ids(
                acc_id, main_filter, start, stop, target_move)
            if not move_line_ids:
                res[acc_id] = []
                continue

            lines = self._get_ledger_lines(move_line_ids, acc_id)
            res[acc_id] = lines
        return res

    def _get_ledger_lines(self, move_line_ids, account_id):
        if not move_line_ids:
            return []
        res = self._get_move_line_datas(move_line_ids)
        # computing counter part is really heavy in term of ressouces
        # consuption looking for a king of SQL to help me improve it
        move_ids = [x.get('move_id') for x in res]
        counter_parts = self._get_moves_counterparts(move_ids, account_id)
        for line in res:
            line['counterparts'] = counter_parts.get(line.get('move_id'), '')
        return res


HeaderFooterTextWebKitParser(
    'report.account.account_report_general_ledger_webkit',
    'account.account',
    'addons/account_financial_report_webkit/report/templates/\
                                        account_report_general_ledger.mako',
    parser=GeneralLedgerWebkit)
