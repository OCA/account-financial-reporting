# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Addons modules by CLEARCORP S.A.
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
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

import xlwt
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.account.report.account_financial_report \
    import report_account_common
from openerp.tools.translate import _


class account_financial_xls(report_xls):
    column_sizes = [50, 30, 30, 30, 12]

    def print_title(self, ws, _p, row_position, xlwt, _xs):
        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name = ' - '.join([_p.report_name.upper(),
                                 _p.company.partner_id.name,
                                 _p.company.currency_id.name])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style)
        return row_position

    def print_empty_row(self, ws, row_position):
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                   for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, set_column_size=True)
        return row_position

    def print_header_titles(self, ws, _p, data, row_position, xlwt, _xs):
        cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])

        c_specs = [
            ('coa', 1, 0, 'text', _('Chart of Accounts'),
                None, cell_style_center),
            ('fy', 1, 0, 'text', _('Fiscal Year'),
             None, cell_style_center),
        ]
        df = ' '
        if data['form']['filter'] == 'filter_no':
            df = _('Not filtered')
        if data['form']['filter'] == 'filter_period':
            df = _('Filtered by period')
        if data['form']['filter'] == 'filter_date':
            df = _('Filtered by date')
        c_specs += [
            ('fb', 1, 0, 'text', df, None, cell_style_center),
            ('tm', 1, 0, 'text', _('Target Moves'), None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style)
        return row_position

    def print_header_data(self, ws, _p, data, row_position, xlwt, _xs):
        cell_format = _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('coa', 1, 0, 'text', _p.get_account(data),
             None, cell_style_center),
            ('fy', 1, 0, 'text', _p.get_fiscalyear(data)
             if _p.get_fiscalyear(data) else '-', None, cell_style_center),

        ]
        df = _('From') + ': '
        if data['form']['filter'] == 'filter_no':
            df = ' '
        if data['form']['filter'] == 'filter_period':
            df += _p.get_start_period(data)
            df += ' ' + _('\nTo') + ': '
            df += _p.get_end_period(data)
        if data['form']['filter'] == 'filter_date':
            df += _p.get_start_date(data)
            df += ' ' + _('\nTo') + ': '
            df += _p.get_end_date(data)
        c_specs += [
            ('fb', 1, 0, 'text', df, None, cell_style_center),
            ('tm', 1, 0, 'text', _p.get_target_move(data),
                None, cell_style_center),
        ]

        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style)
        return row_position

    def print_account_header(self, ws, _p, data, row_position, xlwt, _xs):
        cell_format = _xs['bold'] + _xs['fill'] + \
            _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        # cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        if data['form']['debit_credit'] == 1:
            c_specs = [
                ('account', 1, 0, 'text', _('Account')),
                ('debit', 1, 0, 'text', _('Debit'), None, cell_style_right),
                ('credit', 1, 0, 'text', _('Credit'), None, cell_style_right),
                ('balance', 1, 0, 'text', _('Balance'),
                    None, cell_style_right),
            ]

        if not data['form']['enable_filter'] and \
                not data['form']['debit_credit']:
            c_specs = [
                ('account', 3, 0, 'text', _('Account')),
                ('balance', 1, 0, 'text', _('Balance'),
                    None, cell_style_right),
            ]
        if data['form']['enable_filter'] == 1 and \
                not data['form']['debit_credit']:
            c_specs = [
                ('account', 2, 0, 'text', _('Account')),
                ('balance', 1, 0, 'text', _('Balance'),
                    None, cell_style_right),
            ]
            comparision = data['form']['label_filter']
            c_specs += [
                ('comp', 1, 0, 'text', comparision, None, cell_style_right),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style)
        return row_position

    def print_row_code_account(self, ws, current_account, row_position, _xs,
                               xlwt):
        cell_format = _xs['xls_title'] + _xs['bold'] + \
            _xs['fill'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        c_specs = [
            ('acc_title', 4, 0, 'text', ' - '.join([current_account.code,
                                                    current_account.name])), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, cell_style)
        return row_position

    def print_row_name_account(self, ws, line, row_position, _xs,
                               xlwt, data):
        cell_format = _xs['bold'] + \
            _xs['fill'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        regular_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        if data['form']['debit_credit'] == 1:
            c_specs = [
                ('acc_title', 1, 0, 'text', ' - '.join([line.get('name')])),
                ('debit', 1, 0, 'number', line.get('debit', 0.0),
                    None, regular_cell_style_decimal),
                ('credit', 1, 0, 'number', line.get('credit', 0.0),
                 None, regular_cell_style_decimal),
                ('balance', 1, 0, 'number', line.get('balance', 0.0),
                    None, regular_cell_style_decimal),
             ]
        if not data['form']['enable_filter'] and \
                not data['form']['debit_credit']:
            account_span = 3
            c_specs = [
                    ('acc_title', account_span, 0, 'text',
                        line.get('name') if line.get('name') else
                        _('Unallocated')),
                    ('balance', 1, 0, 'number', line.get('balance', 0.0),
                        None, regular_cell_style_decimal),
            ]
        if data['form']['enable_filter'] == 1 and \
                not data['form']['debit_credit']:
            account_span = 2
            c_specs = [
                ('acc_title', account_span, 0, 'text',
                    line.get('name') if line.get('name') else
                    _('Unallocated')),
                ('balance', 1, 0, 'number', line.get('balance', 0.0),
                    None, regular_cell_style_decimal),
            ]
            c_specs += [
                ('cmp', 1, 0, 'number', line.get('balance_cmp', 0.0),
                    None, regular_cell_style_decimal),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, cell_style)
        return row_position

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        # Initialization
        report_name = data['form']['account_report_id']
        _p['report_name'] = report_name[1]
        ws = wb.add_sheet(_p.report_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        # Print Title
        row_pos = self.print_title(ws, _p, row_pos, xlwt, _xs)
        # Print empty row to define column sizes
        row_pos = self.print_empty_row(ws, row_pos)
        # Print Header Table titles (Fiscal Year - Accounts Filter - Periods
        # Filter...)
        row_pos = self.print_header_titles(ws, _p, data, row_pos, xlwt, _xs)
        # Print Header Table data
        row_pos = self.print_header_data(
            ws, _p, data, row_pos, xlwt, _xs)
        # Freeze the line
        ws.set_horz_split_pos(row_pos)

        # cell styles for account data
        regular_cell_format = _xs['borders_all']
        regular_cell_style = xlwt.easyxf(regular_cell_format)
        regular_cell_style_decimal = xlwt.easyxf(
            regular_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        row_pos += 1
        for current_account in objects:

            # print row: Code - Account name
            row_pos = self.print_row_code_account(
                ws, current_account, row_pos, _xs, xlwt)

            # Print row: Titles "Account-Balance
            # Account-Debit-Credit-Balance"
            # Account-Balance-Comparison"
            row_pos = self.print_account_header(
                ws, _p, data, row_pos, xlwt, _xs)
            lines = _p.get_lines(data)
            for line in lines:
                c_specs = []
                if line['level'] == 0:
                    continue
                else:
                    if data['form']['debit_credit'] == 1:
                        if not line.get('level') > 3:
                            row_pos = self.print_row_name_account(
                                ws, line, row_pos, _xs, xlwt, data)
                        if line.get('level') > 3:
                            c_specs = [
                                ('acc_title', 1, 0, 'text',
                                    line.get('name') if line.get('name')
                                    else _('Unallocated'))]
                            c_specs += [
                                ('debit', 1, 0, 'number',
                                    line.get('debit', 0.0),
                                    None, regular_cell_style_decimal),
                                ('credit', 1, 0, 'number',
                                    line.get('credit', 0.0),
                                    None, regular_cell_style_decimal),
                                ('balance', 1, 0, 'number',
                                    line.get('balance', 0.0),
                                    None, regular_cell_style_decimal),
                                ]
                            row_data = self.xls_row_template(
                                c_specs, [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(
                                ws, row_pos, row_data, regular_cell_style)

                    if not data['form']['enable_filter'] \
                            and not data['form']['debit_credit']:
                        if not line.get('level') > 3:
                            row_pos = self.print_row_name_account(
                                ws, line, row_pos, _xs, xlwt, data)
                        if line.get('level') > 3:
                            c_specs = [
                                ('acc_title', 3, 0, 'text',
                                    line.get('name') if line.get('name')
                                    else _('Unallocated')),
                                ('balance', 1, 0, 'number',
                                    line.get('balance', 0.0),
                                    None, regular_cell_style_decimal),
                            ]
                            row_data = self.xls_row_template(
                                c_specs, [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(
                                ws, row_pos, row_data, regular_cell_style)

                    if data['form']['enable_filter'] == 1 \
                            and not data['form']['debit_credit']:
                        if not line.get('level') > 3:
                            row_pos = self.print_row_name_account(
                                ws, line, row_pos, _xs, xlwt, data)
                        if line.get('level') > 3:
                            c_specs = [
                                ('acc_title', 2, 0, 'text',
                                    line.get('name') if line.get('name') else
                                    _('Unallocated')),
                                ('balance', 1, 0, 'number',
                                    line.get('balance', 0.0),
                                    None, regular_cell_style_decimal),
                            ]
                            c_specs += [
                                ('cmp', 1, 0, 'number',
                                    line.get('balance_cmp', 0.0),
                                    None, regular_cell_style_decimal),
                            ]
                            row_data = self.xls_row_template(
                                c_specs, [x[0] for x in c_specs])
                            row_pos = self.xls_write_row(
                                ws, row_pos, row_data, regular_cell_style)

account_financial_xls('report.account.report_financial_xls',
                      'account.account',
                      parser=report_account_common)
