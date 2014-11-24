# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import xlwt
from openerp.osv import orm
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.tools.translate import translate
import logging
_logger = logging.getLogger(__name__)

_ir_translation_name = 'trial.balance.period.xls'


class trial_balance_period_xls_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        if context is None:
            context = {}
        super(trial_balance_period_xls_parser, self).__init__(
            cr, uid, name, context=context)
        self.context = context
        self.localcontext.update({
            '_': self._,
        })

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(
            self.cr, _ir_translation_name, 'report', lang, src) or src

    def _get_selection_label(self, object, field, val, context=None):
        """ return label of selection list in language of the user """
        field_dict = self.pool.get(object._name).fields_get(
            self.cr, self.uid, allfields=[field], context=context)
        result_list = field_dict[field]['selection']
        result = filter(lambda x: x[0] == val, result_list)[0][1]
        return result

    def _query_get(self, account, period, data):
        query_start = \
            "SELECT COALESCE(SUM(aml.debit), 0) AS debit, " \
            "COALESCE(SUM(aml.credit), 0) AS credit " \
            "FROM account_move_line aml " \
            "INNER JOIN account_journal aj ON aml.journal_id = aj.id " \
            "INNER JOIN account_move am ON aml.move_id = am.id " \
            "INNER JOIN account_account aa ON aml.account_id = aa.id " \
            "INNER JOIN account_period ap ON aml.period_id = ap.id " \
            "WHERE aa.id = %s AND ap.id = %s " % (account.id, period.id)
        if data['move_states'] == 'posted':
            move_selection = "AND am.state = 'posted' "
        else:
            move_selection = ''
        return query_start + move_selection

    def set_context(self, objects, data, ids, report_type=None):
        super(trial_balance_period_xls_parser, self).set_context(
            objects, data, ids)
        cr = self.cr
        uid = self.uid
        context = self.context
        _ = self._

        acc_obj = self.pool.get('account.account')
        company_obj = self.pool.get('res.company')
        fy_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')

        company_id = data['company_id']
        company = company_obj.browse(cr, uid, company_id, context=context)
        period_ids = data['period_ids']
        fiscalyear_id = data['fiscalyear_id']
        move_states = data['move_states']
        level = data['level']

        fiscalyear = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
        fy_code = fiscalyear.code
        report_name = (' - ').join([
            company.name,
            _('Fiscal Year') + ' %s ' % fy_code,
            _('Trial Balance by Period'),
            move_states == ['posted'] and _('All Posted Entries')
            or _('All Entries'),
            company.currency_id.name,
            ])
        periods = period_obj.browse(cr, uid, period_ids, context=context)

        def _child_get(account):
            """ get all (direct & indirect) children of an account """
            accounts = []
            for child in account.child_parent_ids + account.child_consol_ids:
                accounts.append(child)
                accounts += _child_get(child)
            return accounts

        accounts = []
        for account in acc_obj.browse(cr, uid, ids, context):
            accounts.append({
                'account': account,
                'children': _child_get(account),
            })

        accounts_data = []
        for entry in accounts:
            account = entry['account']
            assert account.type == 'view', "Only accounts of type 'view' " \
                "can be selected via the report selection screen."
            account_data = {
                'top': True,
                'account': account,
                'zeros': False,
                'periods_data': [{'code': p.code} for p in periods]
            }
            accounts_data.append(account_data)

            for account in entry['children']:
                if account.type == 'view':
                    zeros = False
                else:
                    zeros = True
                account_data = {
                    'account': account,
                }
                periods_data = []
                for period in periods:
                    period_data = {
                        'code': period.code,
                    }
                    if account.type != 'view':
                        cr.execute(self._query_get(account, period, data))
                        res = cr.dictfetchone()
                        debit = res['debit']
                        credit = res['credit']
                        period_data.update({
                            'debit': debit,
                            'credit': credit,
                        })
                        if debit or credit:
                            zeros = False
                    periods_data.append(period_data)
                account_data.update({
                    'periods_data': periods_data,
                    'zeros': zeros
                })
                accounts_data.append(account_data)

        # calculate view totals
        def _total(x, p, field, total=0.0):
            """ get sum(field) of the child accounts """
            account_start = accounts_data[x]['account']
            level_start = account_start.level
            view_stack = [account_start]
            for y, entry in enumerate(accounts_data[x + 1:], start=x + 1):
                account = entry['account']
                if account.level <= level_start:
                    break
                if account.type == 'view':
                    if account.parent_id == view_stack[-1]:
                        view_stack.append(account)
                    elif account != view_stack[-1]:
                        view_stack.pop()
                        view_stack.append(account)
                else:
                    total += entry['periods_data'][p][field]
            return total

        for i, entry in enumerate(accounts_data):
            account = entry['account']
            if account.type == 'view':
                zeros = True
                for p, period_data in enumerate(entry['periods_data']):
                    debit = _total(i, p, 'debit')
                    credit = _total(i, p, 'credit')
                    period_data['debit'] = debit
                    period_data['credit'] = credit
                    if debit or credit:
                        zeros = False
                entry['zeros'] = zeros

        # remove 'zeros' entries and entries higher than wizard level
        accounts_data = filter(lambda x: not x['zeros'], accounts_data)
        if level:
            accounts_data = filter(
                lambda x: x['account'].level <= level, accounts_data)
        if not accounts_data:
            raise orm.except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))

        # calculate relative child row positions
        row_pos_table = dict((x, []) for x in range(len(accounts_data)))
        for x, entry in enumerate(accounts_data):
            account = entry['account']
            if entry.get('top'):
                level_stack = [(x, account)]
            else:
                if (account.level > level_stack[-1][1].level and
                        account.parent_id == level_stack[-1][1]):
                    row_pos_table[level_stack[-1][0]].append(
                        x - level_stack[-1][0])
                    if account.type == 'view':
                        level_stack.append((x, account))
                else:
                    if account.type == 'view':
                        while level_stack[-1][1].level >= account.level:
                            level_stack.pop()
                        row_pos_table[level_stack[-1][0]].append(
                            x - level_stack[-1][0])
                        level_stack.append((x, account))

        for x, entry in enumerate(accounts_data):
            account = entry['account']
            entry['account_type'] = self._get_selection_label(
                acc_obj, 'type', account.type, context)
            if account.type == 'view':
                entry['child_row_pos'] = row_pos_table[x]

        accounts_data[-1].update({'last': True})

        self.localcontext.update({
            'fy_code': fy_code,
            'report_name': report_name,
            'periods': periods,
            'accounts_data': accounts_data,
        })


class trial_balance_period_xls(report_xls):

    _column_size_acc_code = 12
    _column_size_acc_name = 60
    _column_size_values = 17
    _column_size_type = 12
    _column_size_level = 10

    def __init__(self, name, table, rml=False,
                 parser=False, header=True, store=False):
        super(trial_balance_period_xls, self).__init__(
            name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        _xs.update({
            'fill_grey': 'pattern: pattern solid, fore_color 22;',
            'fill_blue': 'pattern: pattern solid, fore_color 27;',
            'borders_all_black':
                'borders: left thin, right thin, top thin, bottom thin;',
            'borders_left_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (0, self._bc, self._bc, self._bc),
            'borders_right_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (self._bc, 0, self._bc, self._bc),
            'borders_left_right_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (0, 0, self._bc, self._bc),
            'borders_top_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (self._bc, self._bc, 0, self._bc),
            'borders_bottom_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (self._bc, self._bc, self._bc, 0),
            'borders_left_top_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (0, self._bc, 0, self._bc),
            'borders_right_top_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (self._bc, 0, 0, self._bc),
            'borders_left_right_top_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (0, 0, 0, self._bc),
            'borders_left_bottom_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (0, self._bc, self._bc, 0),
            'borders_right_bottom_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (self._bc, 0, self._bc, 0),
            'borders_left_right_bottom_black':
                'borders: left thin, right thin, top thin, bottom thin, '
                'left_colour %s, right_colour %s, '
                'top_colour %s, bottom_colour %s;'
                % (0, 0, self._bc, 0),
        })

        # Period Header format
        ph_cell_format = _xs['bold'] + _xs['fill_grey'] + \
            _xs['borders_all_black']
        self.ph_empty2_cell_style = xlwt.easyxf(
            'borders: right thin, right_colour 0;')
        self.ph_cell_style = xlwt.easyxf(ph_cell_format)
        self.ph_cell_style_center = xlwt.easyxf(
            ph_cell_format + _xs['center'])

        # Values Header format
        vh_cell_format = _xs['bold'] + _xs['fill_blue']
        self.vh_code_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_left_top_black'])
        self.vh_account_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_right_top_black'])
        self.vh_debit_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_left_top_black'] + _xs['right'])
        self.vh_credit_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_top_black'] + _xs['right'])
        self.vh_balance_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_right_top_black'] + _xs['right'])
        self.vh_type_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_left_right_top_black'] +
            _xs['center'])
        self.vh_level_cell_style = xlwt.easyxf(
            vh_cell_format + _xs['borders_left_right_top_black'] +
            _xs['center'])

        # Column Data format for accounts of type View
        av_cell_format = _xs['bold'] + _xs['fill']
        self.av_code_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_left_black'])
        self.av_account_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_right_black'])
        self.av_debit_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_left_black'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.av_credit_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_all'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.av_balance_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_right_black'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.av_type_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_left_right_black'] + _xs['center'])
        self.av_level_cell_style = xlwt.easyxf(
            av_cell_format + _xs['borders_left_right_black'] + _xs['center'])
        self.av_type_cell_style_last = xlwt.easyxf(
            av_cell_format + _xs['borders_left_right_bottom_black'] +
            _xs['center'])
        self.av_level_cell_style_last = xlwt.easyxf(
            av_cell_format + _xs['borders_left_right_bottom_black'] +
            _xs['center'])

        # Column Data format for regular accounts
        self.ar_code_cell_style = xlwt.easyxf(_xs['borders_left_black'])
        self.ar_account_cell_style = xlwt.easyxf(_xs['borders_right_black'])
        self.ar_debit_cell_style = xlwt.easyxf(
            _xs['borders_left_black'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.ar_credit_cell_style = xlwt.easyxf(
            _xs['borders_all'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.ar_balance_cell_style = xlwt.easyxf(
            _xs['borders_right_black'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.ar_type_cell_style = xlwt.easyxf(
            _xs['borders_left_right_black'] + _xs['center'])
        self.ar_level_cell_style = xlwt.easyxf(
            _xs['borders_left_right_black'] + _xs['center'])
        self.ar_type_cell_style_last = xlwt.easyxf(
            _xs['borders_left_right_bottom_black'] + _xs['center'])
        self.ar_level_cell_style_last = xlwt.easyxf(
            _xs['borders_left_right_bottom_black'] + _xs['center'])

        # totals
        tot_cell_format = _xs['bold'] + _xs['fill_blue']
        self.tot_code_cell_style = xlwt.easyxf(
            tot_cell_format + _xs['borders_left_bottom_black'])
        self.tot_account_cell_style = xlwt.easyxf(
            tot_cell_format + _xs['borders_right_bottom_black'])
        self.tot_debit_cell_style = xlwt.easyxf(
            tot_cell_format + _xs['borders_left_bottom_black'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.tot_credit_cell_style = xlwt.easyxf(
            tot_cell_format + _xs['borders_bottom_black'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self.tot_balance_cell_style = xlwt.easyxf(
            tot_cell_format + _xs['borders_right_bottom_black'] +
            _xs['right'],
            num_format_str=report_xls.decimal_format)

    def _tb_report_title(self, ws, _p, row_pos, _xs):

        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name = _p.report_name
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)

        # write empty row to define column sizes
        c_sizes = [self._column_size_acc_code, self._column_size_acc_name] + \
            3 * (len(_p.periods) + 1) * [self._column_size_values] + \
            [self._column_size_type, self._column_size_level]
        c_specs = [
            ('empty%s' % i, 1, c_sizes[i], 'text', None)
            for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, set_column_size=True)

        return row_pos + 1

    def _tb_periods_header(self, ws, _p, row_pos, _xs):
        _ = _p._
        c_specs = [
            ('empty1', 1, 0, 'text', None),
            ('empty2', 1, 0, 'text', None, None, self.ph_empty2_cell_style),
        ]
        for p in _p.periods:
            c_specs.append((p.code, 3, 0, 'text', p.code,
                            None, self.ph_cell_style_center))
        c_specs.append(('totals', 3, 0, 'text', _("Totals"),
                        None, self.ph_cell_style_center))
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data)
        return row_pos

    def _tb_values_header(self, ws, _p, row_pos, _xs):
        _ = _p._
        c_specs = [
            ('code', 1, 0, 'text', _("Code"), None, self.vh_code_cell_style),
            ('account', 1, 0, 'text', _("Account"), None,
             self.vh_account_cell_style),
        ]
        for i in range(len(_p.periods) + 1):
            c_specs += [
                ('debit%s' % i, 1, 0, 'text', _("Debit"),
                 None, self.vh_debit_cell_style),
                ('credit%s' % i, 1, 0, 'text', _("Credit"),
                 None, self.vh_credit_cell_style),
                ('balance%s' % i, 1, 0, 'text', _("Balance"),
                 None, self.vh_balance_cell_style),
            ]
        c_specs += [
            ('type', 1, 0, 'text', _("Type"), None, self.vh_type_cell_style),
            ('level', 1, 0, 'text', _("Level"),
             None, self.vh_level_cell_style),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data)
        ws.set_vert_split_pos(2)
        ws.set_horz_split_pos(row_pos)
        return row_pos

    def _tb_account_data(self, ws, _p, row_pos, _xs, entry):
        account = entry['account']

        av_style = account.type == 'view' and True or False
        if av_style:
            code_cell_style = self.av_code_cell_style
            account_cell_style = self.av_account_cell_style
            debit_cell_style = self.av_debit_cell_style
            credit_cell_style = self.av_credit_cell_style
            balance_cell_style = self.av_balance_cell_style
            type_cell_style = entry.get('last') and \
                self.av_type_cell_style_last or self.av_type_cell_style
            level_cell_style = entry.get('last') and \
                self.av_level_cell_style_last or self.av_level_cell_style
        else:
            code_cell_style = self.ar_code_cell_style
            account_cell_style = self.ar_account_cell_style
            debit_cell_style = self.ar_debit_cell_style
            credit_cell_style = self.ar_credit_cell_style
            balance_cell_style = self.ar_balance_cell_style
            type_cell_style = entry.get('last') and \
                self.ar_type_cell_style_last or self.ar_type_cell_style
            level_cell_style = entry.get('last') and \
                self.ar_level_cell_style_last or self.ar_level_cell_style

        if entry.get('child_row_pos'):
            child_row_pos = [row_pos + p for p in entry['child_row_pos']]
            c_specs = [
                ('code', 1, 0, 'text', account.code, None, code_cell_style),
                ('account', 1, 0, 'text', account.name,
                 None, account_cell_style),
            ]
            for i, vals in enumerate(entry['periods_data']):
                debit_pos = 2 + i * 3
                credit_pos = debit_pos + 1
                debit_cell = rowcol_to_cell(row_pos, debit_pos)
                credit_cell = rowcol_to_cell(row_pos, credit_pos)
                bal_formula = debit_cell + '-' + credit_cell
                if i == 0:
                    debit_total_formula = debit_cell
                    credit_total_formula = credit_cell
                else:
                    debit_total_formula += '+' + debit_cell
                    credit_total_formula += '+' + credit_cell
                child_debit_cells = [
                    rowcol_to_cell(p, debit_pos) for p in child_row_pos]
                debit_formula = '+'.join(child_debit_cells)
                child_credit_cells = [
                    rowcol_to_cell(p, credit_pos) for p in child_row_pos]
                credit_formula = '+'.join(child_credit_cells)
                c_specs += [
                    ('debit%s' % i, 1, 0, 'number', None,
                     debit_formula, debit_cell_style),
                    ('credit%s' % i, 1, 0, 'number', None,
                     credit_formula, credit_cell_style),
                    ('balance%s' % i, 1, 0, 'number', None,
                     bal_formula, balance_cell_style),
                ]
            debit_pos += 3
            credit_pos = debit_pos + 1
            debit_cell = rowcol_to_cell(row_pos, debit_pos)
            credit_cell = rowcol_to_cell(row_pos, credit_pos)
            bal_formula = debit_cell + '-' + credit_cell
            c_specs += [
                ('total_debit%s' % i, 1, 0, 'number',
                 None, debit_total_formula, debit_cell_style),
                ('total_credit%s' % i, 1, 0, 'number',
                 None, credit_total_formula, credit_cell_style),
                ('total_balance%s' % i, 1, 0, 'number',
                 None, bal_formula, balance_cell_style),
            ]
            c_specs += [
                ('type', 1, 0, 'text', entry['account_type'],
                 None, type_cell_style),
                ('level', 1, 0, 'number', account.level,
                 None, level_cell_style),
            ]
        else:
            c_specs = [
                ('code', 1, 0, 'text', account.code,
                 None, code_cell_style),
                ('account', 1, 0, 'text', account.name,
                 None, account_cell_style),
            ]
            for i, vals in enumerate(entry['periods_data']):
                debit_pos = 2 + i * 3
                credit_pos = debit_pos + 1
                debit_cell = rowcol_to_cell(row_pos, debit_pos)
                credit_cell = rowcol_to_cell(row_pos, credit_pos)
                bal_formula = debit_cell + '-' + credit_cell
                if i == 0:
                    debit_total_formula = debit_cell
                    credit_total_formula = credit_cell
                else:
                    debit_total_formula += '+' + debit_cell
                    credit_total_formula += '+' + credit_cell
                c_specs += [
                    ('debit%s' % i, 1, 0, 'number', vals['debit'],
                     None, debit_cell_style),
                    ('credit%s' % i, 1, 0, 'number', vals['credit'],
                     None, credit_cell_style),
                    ('balance%s' % i, 1, 0, 'number',
                     None, bal_formula, balance_cell_style),
                ]
            debit_pos += 3
            credit_pos = debit_pos + 1
            debit_cell = rowcol_to_cell(row_pos, debit_pos)
            credit_cell = rowcol_to_cell(row_pos, credit_pos)
            bal_formula = debit_cell + '-' + credit_cell
            c_specs += [
                ('total_debit%s' % i, 1, 0, 'number',
                 None, debit_total_formula, debit_cell_style),
                ('total_credit%s' % i, 1, 0, 'number',
                 None, credit_total_formula, credit_cell_style),
                ('total_balance%s' % i, 1, 0, 'number',
                 None, bal_formula, balance_cell_style),
            ]
            c_specs += [
                ('type', 1, 0, 'text', entry['account_type'],
                 None, type_cell_style),
                ('level', 1, 0, 'number', account.level,
                 None, level_cell_style),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data)
        return row_pos

    def _tb_account_totals(self, ws, _p, row_pos, _xs, totals_row_pos):
        c_specs = [
            ('code', 1, 0, 'text', None, None, self.tot_code_cell_style),
            ('account', 1, 0, 'text', None,
             None, self.tot_account_cell_style),
        ]
        for i in range(len(_p.periods) + 1):
            debit_pos = 2 + i * 3
            credit_pos = debit_pos + 1
            debit_cell = rowcol_to_cell(row_pos, debit_pos)
            credit_cell = rowcol_to_cell(row_pos, credit_pos)
            bal_formula = debit_cell + '-' + credit_cell
            debit_total_formula = '+'.join(
                [rowcol_to_cell(p, debit_pos) for p in totals_row_pos])
            credit_total_formula = '+'.join(
                [rowcol_to_cell(p, credit_pos) for p in totals_row_pos])
            c_specs += [
                ('debit%s' % i, 1, 0, 'number', None,
                 debit_total_formula, self.tot_debit_cell_style),
                ('credit%s' % i, 1, 0, 'number', None,
                 credit_total_formula, self.tot_credit_cell_style),
                ('balance%s' % i, 1, 0, 'number', None,
                 bal_formula, self.tot_balance_cell_style),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data)
        return row_pos

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        sheet_name = _p.fy_code[:31].replace('/', '-')
        ws = wb.add_sheet(sheet_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Header
        row_pos = self._tb_report_title(ws, _p, row_pos, _xs)
        row_pos = self._tb_periods_header(ws, _p, row_pos, _xs)
        row_pos = self._tb_values_header(ws, _p, row_pos, _xs)

        # Data
        totals_row_pos = []
        for entry in _p.accounts_data:
            if entry.get('top'):
                totals_row_pos.append(row_pos)
            row_pos = self._tb_account_data(ws, _p, row_pos, _xs, entry)

        # Totals
        row_pos = self._tb_account_totals(
            ws, _p, row_pos, _xs, totals_row_pos)

trial_balance_period_xls(
    'report.account.trial.balance.period.xls',
    'account.journal',
    parser=trial_balance_period_xls_parser)
