##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>),
#    Copyright (C) 2012 Therp BV (<http://therp.nl>),
#    Copyright (C) 2013 Agile Business Group sagl
#    (<http://www.agilebg.com>) (<lorenzo.battistini@agilebg.com>)
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

import time
from openerp.report import report_sxw
from .common_report_header import common_report_header
from openerp.tools.translate import _


class report_pl_account_horizontal(report_sxw.rml_parse, common_report_header):

    def __init__(self, cr, uid, name, context=None):
        super(report_pl_account_horizontal, self).__init__(
            cr, uid, name, context=context)
        self.result_sum_dr = 0.0
        self.result_sum_cr = 0.0
        self.res_pl = {}
        self.result = {}
        self.result_temp = []
        self.localcontext.update({
            'time': time,
            'get_lines': self.get_lines,
            'get_lines_another': self.get_lines_another,
            'get_data': self.get_data,
            'sum_dr': self.sum_dr,
            'sum_cr': self.sum_cr,
            'final_result': self.final_result,
            'get_fiscalyear': self._get_fiscalyear,
            'get_account': self._get_account,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_sortby': self._get_sortby,
            'get_filter': self._get_filter,
            'get_start_date': self._get_start_date,
            'get_end_date': self._get_end_date,
            'get_target_move': self._get_target_move,
            'get_trans': self._get_trans
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and data['form'][
                'chart_account_id'] and [data['form']['chart_account_id'][0]] \
                or []
            objects = self.pool.get('account.account').browse(
                self.cr, self.uid, new_ids)
            lang_dict = self.pool.get('res.users').read(
                self.cr, self.uid, self.uid, ['context_lang'])
            data['lang'] = lang_dict.get('context_lang') or False
        return super(report_pl_account_horizontal, self).set_context(
            objects, data, new_ids, report_type=report_type)

    def final_result(self):
        return self.res_pl

    def sum_dr(self):
        if self.res_pl['type'] == _('Net Profit'):
            self.result_sum_dr += self.res_pl['balance']
        return self.result_sum_dr

    def sum_cr(self):
        if self.res_pl['type'] == _('Net Loss'):
            self.result_sum_cr += self.res_pl['balance']
        return self.result_sum_cr

    def _get_trans(self, source):
        return _(source)

    def get_data(self, data):
        def get_account_repr(account, account_type):
            return {
                'code': account.code,
                'name': account.name,
                'level': account.level,
                'balance': account.balance and (
                    account_type == 'income' and -1 or 1) * account.balance,
                'type': account.type,
            }

        cr, uid = self.cr, self.uid

        account_pool = self.pool['account.account']
        currency_pool = self.pool['res.currency']

        types = [
            'expense',
            'income'
        ]

        ctx = self.context.copy()
        ctx['fiscalyear'] = data['form'].get('fiscalyear_id', False)
        if ctx['fiscalyear']:
            ctx['fiscalyear'] = ctx['fiscalyear'][0]

        if data['form']['filter'] == 'filter_period':
            ctx['periods'] = data['form'].get('periods', False)
        elif data['form']['filter'] == 'filter_date':
            ctx['date_from'] = data['form'].get('date_from', False)
            ctx['date_to'] = data['form'].get('date_to', False)
        ctx['state'] = data['form'].get('target_move', 'all')
        cal_list = {}
        account_id = data['form'].get('chart_account_id', False)
        if account_id:
            account_id = account_id[0]
        account_ids = account_pool._get_children_and_consol(
            cr, uid, account_id, context=ctx)
        accounts = account_pool.browse(cr, uid, account_ids, context=ctx)

        for typ in types:
            accounts_temp = []
            for account in accounts:
                if (account.user_type.report_type) and (
                    account.user_type.report_type == typ
                ):
                    currency = (
                        account.currency_id and account.currency_id
                        or account.company_id.currency_id)
                    if typ == 'expense' and account.type != 'view' and (
                        account.debit != account.credit
                    ):
                        self.result_sum_dr += account.debit - account.credit
                    if typ == 'income' and account.type != 'view' and (
                        account.debit != account.credit
                    ):
                        self.result_sum_cr += account.credit - account.debit
                    if data['form']['display_account'] == 'bal_movement':
                        if (
                            not currency_pool.is_zero(
                                self.cr, self.uid, currency, account.credit)
                        ) or (
                            not currency_pool.is_zero(
                                self.cr, self.uid, currency, account.debit)
                        ) or (
                            not currency_pool.is_zero(
                                self.cr, self.uid, currency, account.balance)
                        ):
                            accounts_temp.append(
                                get_account_repr(account, typ))
                    elif data['form']['display_account'] == 'bal_solde':
                        if not currency_pool.is_zero(
                            self.cr, self.uid, currency, account.balance
                        ):
                            accounts_temp.append(
                                get_account_repr(account, typ))
                    else:
                        accounts_temp.append(get_account_repr(account, typ))
            if self.result_sum_dr > self.result_sum_cr:
                self.res_pl['type'] = _('Net Loss')
                self.res_pl['balance'] = (
                    self.result_sum_dr - self.result_sum_cr)
            else:
                self.res_pl['type'] = _('Net Profit')
                self.res_pl['balance'] = (
                    self.result_sum_cr - self.result_sum_dr)
            self.result[typ] = accounts_temp
            cal_list[typ] = self.result[typ]
        if cal_list:
            temp = {}
            for i in range(
                0, max(len(cal_list['expense']), len(cal_list['income']))
            ):
                if i < len(cal_list['expense']) and i < len(
                    cal_list['income']
                ):
                    temp = {
                        'code': cal_list['expense'][i]['code'],
                        'name': cal_list['expense'][i]['name'],
                        'level': cal_list['expense'][i]['level'],
                        'balance': cal_list['expense'][i]['balance'],
                        'type': cal_list['expense'][i]['type'],
                        'code1': cal_list['income'][i]['code'],
                        'name1': cal_list['income'][i]['name'],
                        'level1': cal_list['income'][i]['level'],
                        'balance1': cal_list['income'][i]['balance'],
                        'type1': cal_list['income'][i]['type'],
                    }
                    self.result_temp.append(temp)
                else:
                    if i < len(cal_list['income']):
                        temp = {
                            'code': '',
                            'name': '',
                            'level': False,
                            'balance': False,
                            'type': False,
                            'code1': cal_list['income'][i]['code'],
                            'name1': cal_list['income'][i]['name'],
                            'level1': cal_list['income'][i]['level'],
                            'balance1': cal_list['income'][i]['balance'],
                            'type1': cal_list['income'][i]['type'],
                        }
                        self.result_temp.append(temp)
                    if i < len(cal_list['expense']):
                        temp = {
                            'code': cal_list['expense'][i]['code'],
                            'name': cal_list['expense'][i]['name'],
                            'level': cal_list['expense'][i]['level'],
                            'balance': cal_list['expense'][i]['balance'],
                            'type': cal_list['expense'][i]['type'],
                            'code1': '',
                            'name1': '',
                            'level1': False,
                            'balance1': False,
                            'type1': False,
                        }
                        self.result_temp.append(temp)
        return None

    def get_lines(self):
        return self.result_temp

    def get_lines_another(self, group):
        return self.result.get(group, [])

report_sxw.report_sxw(
    'report.account.profit_horizontal', 'account.account',
    'addons/account_financial_report_horizontal/report/'
    'account_profit_horizontal.rml',
    parser=report_pl_account_horizontal, header='internal landscape')

report_sxw.report_sxw(
    'report.account.profit_loss', 'account.account',
    'addons/account_financial_report_horizontal/report/'
    'account_profit_loss.rml',
    parser=report_pl_account_horizontal, header='internal')
