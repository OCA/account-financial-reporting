# -*- encoding: utf-8 -*-
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

from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from mako.template import Template


from openerp.modules.registry import RegistryManager
from openerp.osv import osv
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.addons.report_webkit import report_helper
from .common_partner_reports import CommonPartnersReportHeaderWebkit
from .webkit_parser_header_fix import HeaderFooterTextWebKitParser
from openerp.modules.module import get_module_resource


def get_mako_template(obj, *args):
    template_path = get_module_resource(*args)
    return Template(filename=template_path, input_encoding='utf-8')


report_helper.WebKitHelper.get_mako_template = get_mako_template


class PartnersOpenInvoicesWebkit(report_sxw.rml_parse,
                                 CommonPartnersReportHeaderWebkit):

    def __init__(self, cursor, uid, name, context):
        super(PartnersOpenInvoicesWebkit, self).__init__(
            cursor, uid, name, context=context)
        self.pool = RegistryManager.get(self.cr.dbname)
        self.cursor = self.cr

        company = self.pool.get('res.users').browse(
            self.cr, uid, uid, context=context).company_id
        header_report_name = ' - '.join((_('OPEN INVOICES REPORT'),
                                        company.name,
                                        company.currency_id.name))

        footer_date_time = self.formatLang(
            str(datetime.today()), date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('Open Invoices Report'),
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'amount_currency': self._get_amount_currency,
            'display_partner_account': self._get_display_partner_account,
            'display_target_move': self._get_display_target_move,
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

    def _group_lines_by_currency(self, account_br, ledger_lines):
        account_br.grouped_ledger_lines = {}
        if not ledger_lines:
            return
        for part_id, plane_lines in ledger_lines.items():
            account_br.grouped_ledger_lines[part_id] = []
            plane_lines.sort(key=itemgetter('currency_code'))
            for curr, lines in groupby(plane_lines,
                                       key=itemgetter('currency_code')):
                tmp = [x for x in lines]
                account_br.grouped_ledger_lines[part_id].append(
                    (curr, tmp))  # I want to reiter many times

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will
           be used by mako template"""
        new_ids = data['form']['chart_account_id']
        # Account initial balance memoizer
        init_balance_memoizer = {}
        # Reading form
        main_filter = self._get_form_param('filter', data, default='filter_no')
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)
        partner_ids = self._get_form_param('partner_ids', data)
        result_selection = self._get_form_param('result_selection', data)
        date_until = self._get_form_param('until_date', data)
        chart_account = self._get_chart_account_id_br(data)
        group_by_currency = self._get_form_param('group_by_currency', data)

        if main_filter == 'filter_no' and fiscalyear:
            start_period = self._get_first_special_period()
            stop_period = self.get_last_fiscalyear_period(fiscalyear)

        # Retrieving accounts
        filter_type = ('payable', 'receivable')
        if result_selection == 'customer':
            filter_type = ('receivable',)
        if result_selection == 'supplier':
            filter_type = ('payable',)

        account_ids = self.get_all_accounts(
            new_ids, exclude_type=['view'], only_type=filter_type)

        if not account_ids:
            raise osv.except_osv(_('Error'), _('No accounts to print.'))

        # computation of ledeger lines
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period
        ledger_lines_memoizer = self._compute_open_transactions_lines(
            account_ids, main_filter, target_move, start, stop, date_until,
            partner_filter=partner_ids)
        objects = self.pool.get('account.account').browse(self.cursor,
                                                          self.uid,
                                                          account_ids)

        ledger_lines = {}
        init_balance = {}
        partners_order = {}
        for account in objects:
            ledger_lines[account.id] = ledger_lines_memoizer.get(account.id,
                                                                 {})
            init_balance[account.id] = init_balance_memoizer.get(account.id,
                                                                 {})
            # we have to compute partner order based on inital balance
            # and ledger line as we may have partner with init bal
            # that are not in ledger line and vice versa
            ledg_lines_pids = ledger_lines_memoizer.get(account.id, {}).keys()
            non_null_init_balances = dict([
                (ib, amounts) for ib, amounts
                in init_balance[account.id].iteritems()
                if amounts['init_balance'] or
                amounts['init_balance_currency']])
            init_bal_lines_pids = non_null_init_balances.keys()

            partners_order[account.id] = self._order_partners(
                ledg_lines_pids, init_bal_lines_pids)
            ledger_lines[account.id] = ledger_lines_memoizer.get(account.id,
                                                                 {})
            if group_by_currency:
                self._group_lines_by_currency(
                    account, ledger_lines[account.id])

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'date_until': date_until,
            'partner_ids': partner_ids,
            'chart_account': chart_account,
            'ledger_lines': ledger_lines,
            'init_balance': init_balance,
            'partners_order': partners_order
        })

        return super(PartnersOpenInvoicesWebkit, self).set_context(
            objects, data, new_ids, report_type=report_type)

    def _compute_open_transactions_lines(self, accounts_ids, main_filter,
                                         target_move, start, stop,
                                         date_until=False,
                                         partner_filter=False):
        res = defaultdict(dict)

        # we check if until date and date stop have the same value
        if main_filter in ('filter_period', 'filter_no'):
            date_stop = stop.date_stop
            date_until_match = (date_stop == date_until)

        elif main_filter == 'filter_date':
            date_stop = stop
            date_until_match = (stop == date_until)

        else:
            raise osv.except_osv(_('Unsuported filter'),
                                 _('Filter has to be in filter date, period, \
                                 or none'))

        initial_move_lines_per_account = {}
        if main_filter in ('filter_period', 'filter_no'):
            initial_move_lines_per_account = self._tree_move_line_ids(
                self._partners_initial_balance_line_ids(accounts_ids,
                                                        start,
                                                        partner_filter,
                                                        exclude_reconcile=True,
                                                        force_period_ids=False,
                                                        date_stop=date_stop),
                key='id')

        for account_id in accounts_ids:
            initial_move_lines_ids_per_partner = \
                initial_move_lines_per_account.get(account_id, {})

            # We get the move line ids of the account
            move_line_ids_per_partner = self.get_partners_move_lines_ids(
                account_id, main_filter, start, stop, target_move,
                exclude_reconcile=True, partner_filter=partner_filter)

            if not initial_move_lines_ids_per_partner \
                    and not move_line_ids_per_partner:
                continue
            for partner_id in list(
                    set(initial_move_lines_ids_per_partner.keys() +
                        move_line_ids_per_partner.keys())):
                partner_line_ids = (
                    move_line_ids_per_partner.get(partner_id, []) +
                    initial_move_lines_ids_per_partner.get(partner_id, []))

                clearance_line_ids = []
                if date_until and not date_until_match and partner_line_ids:
                    clearance_line_ids = self._get_clearance_move_line_ids(
                        partner_line_ids, date_stop, date_until)
                    partner_line_ids += clearance_line_ids

                lines = self._get_move_line_datas(list(set(partner_line_ids)))
                for line in lines:
                    if line['id'] in initial_move_lines_ids_per_partner.\
                            get(partner_id, []):
                        line['is_from_previous_periods'] = True
                    if line['id'] in clearance_line_ids:
                        line['is_clearance_line'] = True

                res[account_id][partner_id] = lines
        return res


HeaderFooterTextWebKitParser(
    'report.account.account_report_open_invoices_webkit',
    'account.account',
    'addons/account_financial_report_webkit/report/templates/\
                                        account_report_open_invoices.mako',
    parser=PartnersOpenInvoicesWebkit)
