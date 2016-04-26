# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.trial_balance \
    import TrialBalanceWebkit
from openerp.tools.translate import _
# import logging
# _logger = logging.getLogger(__name__)


class trial_balance_xls(report_xls):
    column_sizes = [12, 60, 17, 17, 17, 17, 17, 17]

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        ws = wb.add_sheet(_p.report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # cf. account_report_trial_balance.mako
        initial_balance_text = {'initial_balance': _('Computed'),
                                'opening_balance': _('Opening Entries'),
                                False: _('No')}

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name = ' - '.join([_p.report_name.upper(),
                                 _p.company.partner_id.name,
                                 _p.company.currency_id.name])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)

        # write empty row to define column sizes
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                   for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, set_column_size=True)

        # Header Table
        cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('fy', 1, 0, 'text', _('Fiscal Year')),
            ('af', 2, 0, 'text', _('Accounts Filter')),
            ('df', 1, 0, 'text', _p.filter_form(data) ==
             'filter_date' and _('Dates Filter') or _('Periods Filter')),
            ('tm', 2, 0, 'text', _('Target Moves'), None, cell_style_center),
            ('ib', 1, 0, 'text', _('Initial Balance'),
             None, cell_style_center),
            ('coa', 1, 0, 'text', _('Chart of Account'),
             None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)

        cell_format = _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('fy', 1, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-'),
            ('af', 2, 0, 'text', _p.accounts(data) and ', '.join(
                [account.code for account in _p.accounts(data)]) or _('All')),
        ]
        df = _('From') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.start_date if _p.start_date else u''
        else:
            df += _p.start_period.name if _p.start_period else u''
        df += ' ' + _('\nTo') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.stop_date if _p.stop_date else u''
        else:
            df += _p.stop_period.name if _p.stop_period else u''
        c_specs += [
            ('df', 1, 0, 'text', df),
            ('tm', 2, 0, 'text', _p.display_target_move(
                data), None, cell_style_center),
            ('ib', 1, 0, 'text', initial_balance_text[
             _p.initial_balance_mode], None, cell_style_center),
            ('coa', 1, 0, 'text', _p.chart_account.name,
             None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)

        # comparison header table
        if _p.comparison_mode in ('single', 'multiple'):
            row_pos += 1
            cell_format_ct = _xs['bold'] + \
                _xs['fill_blue'] + _xs['borders_all']
            cell_style_ct = xlwt.easyxf(cell_format_ct)
            c_specs = [('ct', 8, 0, 'text', _('Comparisons'))]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=cell_style_ct)
            cell_style_center = xlwt.easyxf(cell_format)
            for index, params in enumerate(_p.comp_params):
                c_specs = [
                    ('c', 3, 0, 'text', _('Comparison') + str(index + 1) +
                     ' (C' + str(index + 1) + ')')]
                if params['comparison_filter'] == 'filter_date':
                    c_specs += [('f', 3, 0, 'text', _('Dates Filter') + ': ' +
                                 _p.formatLang(
                                     params['start'], date=True) + ' - ' +
                                 _p.formatLang(params['stop'], date=True))]
                elif params['comparison_filter'] == 'filter_period':
                    c_specs += [('f', 3, 0, 'text', _('Periods Filter') +
                                 ': ' + params['start'].name + ' - ' +
                                 params['stop'].name)]
                else:
                    c_specs += [('f', 3, 0, 'text', _('Fiscal Year') +
                                 ': ' + params['fiscalyear'].name)]
                c_specs += [('ib', 2, 0, 'text', _('Initial Balance') +
                             ': ' +
                             initial_balance_text[
                                 params['initial_balance_mode']])]
                row_data = self.xls_row_template(
                    c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    ws, row_pos, row_data, row_style=cell_style_center)

        row_pos += 1

        # Column Header Row
        cell_format = _xs['bold'] + _xs['fill_blue'] + \
            _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        if len(_p.comp_params) == 2:
            account_span = 3
        else:
            account_span = _p.initial_balance_mode and 2 or 3
        c_specs = [
            ('code', 1, 0, 'text', _('Code')),
            ('account', account_span, 0, 'text', _('Account')),
        ]
        if _p.comparison_mode == 'no_comparison':
            if _p.initial_balance_mode:
                c_specs += [('init_bal', 1, 0, 'text',
                             _('Initial Balance'), None, cell_style_right)]
            c_specs += [
                ('debit', 1, 0, 'text', _('Debit'), None, cell_style_right),
                ('credit', 1, 0, 'text', _('Credit'), None, cell_style_right),
            ]

        if _p.comparison_mode == 'no_comparison' or not _p.fiscalyear:
            c_specs += [('balance', 1, 0, 'text',
                         _('Balance'), None, cell_style_right)]
        else:
            c_specs += [('balance_fy', 1, 0, 'text', _('Balance %s') %
                         _p.fiscalyear.name, None, cell_style_right)]
        if _p.comparison_mode in ('single', 'multiple'):
            for index in range(_p.nb_comparison):
                if _p.comp_params[index][
                    'comparison_filter'] == 'filter_year' \
                        and _p.comp_params[index].get('fiscalyear', False):
                    c_specs += [('balance_%s' % index, 1, 0, 'text',
                                 _('Balance %s') %
                                 _p.comp_params[index]['fiscalyear'].name,
                                 None, cell_style_right)]
                else:
                    c_specs += [('balance_%s' % index, 1, 0, 'text',
                                 _('Balance C%s') % (index + 1), None,
                                 cell_style_right)]
                if _p.comparison_mode == 'single':
                    c_specs += [
                        ('diff', 1, 0, 'text', _('Difference'),
                         None, cell_style_right),
                        ('diff_percent', 1, 0, 'text',
                         _('% Difference'), None, cell_style_center),
                    ]
        c_specs += [('type', 1, 0, 'text', _('Type'), None, cell_style_center)]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style)
        ws.set_horz_split_pos(row_pos)

        last_child_consol_ids = []

        # cell styles for account data
        view_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        view_cell_style = xlwt.easyxf(view_cell_format)
        view_cell_style_center = xlwt.easyxf(view_cell_format + _xs['center'])
        view_cell_style_decimal = xlwt.easyxf(
            view_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        view_cell_style_pct = xlwt.easyxf(
            view_cell_format + _xs['center'], num_format_str='0')
        regular_cell_format = _xs['borders_all']
        regular_cell_style = xlwt.easyxf(regular_cell_format)
        regular_cell_style_center = xlwt.easyxf(
            regular_cell_format + _xs['center'])
        regular_cell_style_decimal = xlwt.easyxf(
            regular_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        regular_cell_style_pct = xlwt.easyxf(
            regular_cell_format + _xs['center'], num_format_str='0')

        for current_account in objects:

            if not _p['to_display_accounts'][current_account.id]:
                continue

            if current_account.type == 'view':
                cell_style = view_cell_style
                cell_style_center = view_cell_style_center
                cell_style_decimal = view_cell_style_decimal
                cell_style_pct = view_cell_style_pct
            else:
                cell_style = regular_cell_style
                cell_style_center = regular_cell_style_center
                cell_style_decimal = regular_cell_style_decimal
                cell_style_pct = regular_cell_style_pct

            comparisons = _p['comparisons_accounts'][current_account.id]

            if current_account.id not in last_child_consol_ids:
                # current account is a not a consolidation child: use its own
                # level
                last_child_consol_ids = [
                    child_consol_id.id for child_consol_id in
                    current_account.child_consol_ids]

            c_specs = [
                ('code', 1, 0, 'text', current_account.code),
                ('account', account_span, 0, 'text', current_account.name),
            ]
            if _p.comparison_mode == 'no_comparison':

                debit_cell = rowcol_to_cell(row_pos, 4)
                credit_cell = rowcol_to_cell(row_pos, 5)
                bal_formula = debit_cell + '-' + credit_cell

                if _p.initial_balance_mode:
                    init_cell = rowcol_to_cell(row_pos, 3)
                    debit_cell = rowcol_to_cell(row_pos, 4)
                    credit_cell = rowcol_to_cell(row_pos, 5)
                    bal_formula = init_cell + '+' + \
                        debit_cell + '-' + credit_cell
                    c_specs += [('init_bal', 1, 0, 'number',
                                 _p['init_balance_'
                                    'accounts'][current_account.id],
                                 None,
                                 cell_style_decimal)]
                c_specs += [
                    ('debit', 1, 0, 'number',
                     _p['debit_accounts'][current_account.id],
                     None, cell_style_decimal),
                    ('credit', 1, 0, 'number',
                     _p['credit_accounts'][current_account.id],
                     None, cell_style_decimal),
                ]
                c_specs += [('balance', 1, 0, 'number', None,
                             bal_formula, cell_style_decimal)]
            else:
                c_specs += [('balance', 1, 0, 'number',
                             _p['balance_accounts'][current_account.id],
                             None, cell_style_decimal)]

            if _p.comparison_mode in ('single', 'multiple'):
                c = 1
                for comp_account in comparisons:
                    c_specs += [('balance_%s' % c, 1, 0, 'number',
                                 comp_account['balance'], None,
                                 cell_style_decimal)]
                    c += 1
                    if _p.comparison_mode == 'single':
                        c_specs += [
                            ('diff', 1, 0, 'number', comp_account[
                             'diff'], None, cell_style_decimal),
                            ('diff_percent', 1, 0, 'number', comp_account[
                             'percent_diff'] and
                             comp_account['percent_diff'] or 0, None,
                             cell_style_pct),
                        ]

            c_specs += [('type', 1, 0, 'text',
                         current_account.type, None, cell_style_center)]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=cell_style)

trial_balance_xls('report.account.account_report_trial_balance_xls',
                  'account.account',
                  parser=TrialBalanceWebkit)
