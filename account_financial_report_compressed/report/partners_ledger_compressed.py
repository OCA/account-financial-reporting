# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Matthieu Dietrich
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

from openerp.tools.translate import _
from openerp.addons.account_financial_report_webkit.\
    report.partners_ledger import PartnersLedgerWebkit
from .webkit_parser_multiple_files import MultipleFilesWebKitParser


class PartnersLedgerWebkitCompressed(PartnersLedgerWebkit):

    def get_account_ids(self, cursor, uid, ids, data, context=None):
        # Retrieve all ids for ZIP report
        new_ids = data['form']['chart_account_id']
        result_selection = self._get_form_param('result_selection', data)
        filter_type = ('payable', 'receivable')
        if result_selection == 'customer':
            filter_type = ('receivable',)
        if result_selection == 'supplier':
            filter_type = ('payable',)
        return self.get_all_accounts(new_ids, exclude_type=['view'],
                                     only_type=filter_type)

    def _create_empty_account(self, account_id):
        # Returns "empty" browse account (no ledger lines)
        empty_account = self.pool.get('account.account').browse(
            self.cursor, self.uid, account_id
        )
        empty_account.ledger_lines = {}
        empty_account.init_balance = {}
        empty_account.partners_order = []
        return empty_account

    def _split_account(self, account):
        # method to split the account according to the number of ledger lines.
        # Here are the rules for the split:
        # - (lines in current object + lines in partner) <= 20000:
        #       add partner in file
        # - (lines in current object + lines in partner) > 20000:
        #       create new object and add partner in it
        # If the partner has more than 20000 lines by itself, it will be alone
        # in a file.

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
        current_line_count = 0
        if account.partners_order and account.partners_order[0][3]:
            partner_start = account.partners_order[0][3].replace('/', '-')
        else:
            partner_start = _('(No Partner)')
        partner_end = partner_start
        for partner_name, p_id, p_ref, p_name in account.partners_order:
            if p_id in account.ledger_lines:
                partner_ledger_lines = account.ledger_lines[p_id]
                if current_line_count + len(partner_ledger_lines) > 20000:
                    # File would be too big; close current and create a new one
                    # Use account for folder name,
                    # partner_start-partner_end for file
                    # partner_start only if only one partner in file
                    file_name = account.code + " - " + \
                        account.name.replace('/', '-') + "/"
                    if partner_start != partner_end:
                        file_name += partner_start + "-" + \
                            partner_end + ".pdf"
                    else:
                        file_name += partner_start + ".pdf"
                    current_account.file_name = file_name
                    # Add account to objects
                    accounts.append(current_account)
                    current_account = self._create_empty_account(account.id)
                    current_line_count = 0
                    if p_name:
                        partner_start = p_name.replace('/', '-')
                    else:
                        partner_start = _('(No Partner)')
                # Common part: add current partner data to current account
                current_line_count += len(partner_ledger_lines)
                current_account.ledger_lines[p_id] = partner_ledger_lines

                # Add to cumulated balance
                cumulated_balance['total_debit'] += \
                    sum(line.get('debit', 0.0)
                        for line in partner_ledger_lines)
                cumulated_balance['total_credit'] += \
                    sum(line.get('credit', 0.0)
                        for line in partner_ledger_lines)
                cumulated_balance['cumul_balance'] += \
                    sum(line.get('balance', 0.0)
                        for line in partner_ledger_lines)
                cumulated_balance['cumul_balance_curr'] += \
                    sum(line.get('amount_currency', 0.0)
                        for line in partner_ledger_lines)

            if p_id in account.init_balance:
                init_balance = account.init_balance[p_id]
                current_account.init_balance[p_id] = init_balance
                # Add to cumulated balance
                cumulated_balance['total_debit'] += \
                    init_balance.get('debit', 0.0)
                cumulated_balance['total_credit'] += \
                    init_balance.get('credit', 0.0)
                cumulated_balance['cumul_balance'] += \
                    init_balance.get('init_balance', 0.0)
                cumulated_balance['cumul_balance_curr'] += \
                    init_balance.get('init_balance_currency', 0.0)
                current_line_count += 1

            current_account.partners_order.append(
                (partner_name, p_id, p_ref, p_name)
            )

            # Empty partner at the end of the order is only in file name
            # if the file started on this partner; otherwise, keep last
            # partner name
            if p_name:
                partner_end = p_name.replace('/', '-')
            elif partner_start == _('(No Partner)'):
                partner_end = _('(No Partner)')

        if current_line_count > 0:
            # Add last file
            file_name = account.code + " - " + \
                account.name.replace('/', '-') + "/"
            if partner_start != partner_end:
                file_name += partner_start + "-" + partner_end + ".pdf"
            else:
                file_name += partner_start + ".pdf"
            current_account.file_name = file_name
            # Add account to objects
            accounts.append(current_account)

        return accounts, cumulated_balance

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each
        browse record that will be used
        by mako template"""
        new_ids = data['form']['chart_account_id']

        # account partner memoizer
        # Reading form
        main_filter = self._get_form_param('filter', data, default='filter_no')
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)
        partner_ids = self._get_form_param('partner_ids', data)
        chart_account = self._get_chart_account_id_br(data)

        if main_filter == 'filter_no' and fiscalyear:
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)

        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period

        # when the opening period is included in the selected range of
        # periods and the opening period contains move lines, we must not
        # compute the initial balance from previous periods
        # but only display the move lines of the opening period
        # we identify them as:
        #  - 'initial_balance' means compute the sums of move lines from
        #                      previous periods
        #  - 'opening_balance' means display the move lines of the opening
        #                      period
        init_balance = main_filter in ('filter_no', 'filter_period')
        initial_balance_mode = init_balance and \
            self._get_initial_balance_mode(start) or False

        initial_balance_lines = {}
        if initial_balance_mode == 'initial_balance':
            initial_balance_lines = self._compute_partners_initial_balances(
                ids, start_period, partner_filter=partner_ids,
                exclude_reconcile=False
            )

        ledger_lines = self._compute_partner_ledger_lines(
            ids, main_filter, target_move, start, stop,
            partner_filter=partner_ids
        )

        account = self.pool.get('account.account').browse(
            self.cursor, self.uid, ids[0]
        )
        account.ledger_lines = ledger_lines.get(account.id, {})
        account.init_balance = initial_balance_lines.get(account.id, {})
        # we have to compute partner order based on inital balance
        # and ledger line as we may have partner with init bal
        # that are not in ledger line and vice versa
        ledg_lines_pids = ledger_lines.get(account.id, {}).keys()
        if initial_balance_mode:
            non_null_init_balances = dict(
                [(ib, amounts) for ib, amounts
                 in account.init_balance.iteritems()
                 if amounts['init_balance'] or amounts['init_balance_currency']
                 ]
            )
            init_bal_lines_pids = non_null_init_balances.keys()
        else:
            account.init_balance = {}
            init_bal_lines_pids = []

        account.partners_order = self._order_partners(
            ledg_lines_pids, init_bal_lines_pids
        )

        # Split account into multiple objects (to avoid a massive file)
        objects, cumulated_balance = self._split_account(account)

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'partner_ids': partner_ids,
            'chart_account': chart_account,
            'initial_balance_mode': initial_balance_mode,
            'cumulated_balance': cumulated_balance,
        })

        # We call the super method of PartnersLedgerWebkit, to avoid
        # retrieving all lines in PartnersLedgerWebkit
        return super(PartnersLedgerWebkit, self).set_context(
            objects, data, new_ids, report_type=report_type
        )


MultipleFilesWebKitParser(
    'report.account.account_report_partners_ledger_compressed',
    'account.account',
    'addons/account_financial_report_webkit/report/'
    'templates/account_report_partners_ledger.mako',
    parser=PartnersLedgerWebkitCompressed)
