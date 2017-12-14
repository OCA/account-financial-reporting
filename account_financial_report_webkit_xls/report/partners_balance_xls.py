# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import xlwt
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.partner_balance \
    import PartnerBalanceWebkit
from openerp.tools.translate import _
# import logging
# _logger = logging.getLogger(__name__)


def display_line(all_comparison_lines):
    return any([line.get('balance') for line in all_comparison_lines])


class PartnersBalanceXls(report_xls):
    column_sizes = [12, 40, 25, 17, 17, 17, 17, 17]

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
            ('fy', 1, 0, 'text', _('Fiscal Year'), None, cell_style_center),
            ('af', 1, 0, 'text', _('Accounts Filter'),
             None, cell_style_center),
            ('df', 1, 0, 'text', _p.filter_form(data) == 'filter_date' and _(
                'Dates Filter') or _('Periods Filter'), None,
             cell_style_center),
            ('pf', 1, 0, 'text', _('Partners Filter'),
             None, cell_style_center),
            ('tm', 1, 0, 'text', _('Target Moves'), None, cell_style_center),
            ('ib', 1, 0, 'text', _('Initial Balance'),
             None, cell_style_center),
            ('coa', 1, 0, 'text', _('Chart of Account'),
             None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style)
        return row_position

    def print_header_data(self, ws, _p, data, row_position, xlwt, _xs,
                          initial_balance_text):
        cell_format = _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('fy', 1, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-',
             None, cell_style_center),
            ('af', 1, 0, 'text', _p.accounts(data) and ', '.join(
                [account.code for account in _p.accounts(data)]) or _('All'),
             None, cell_style_center),
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
            ('df', 1, 0, 'text', df, None, cell_style_center),
            ('tm', 1, 0, 'text', _p.display_partner_account(
                data), None, cell_style_center),
            ('pf', 1, 0, 'text', _p.display_target_move(
                data), None, cell_style_center),
            ('ib', 1, 0, 'text', initial_balance_text[
             _p.initial_balance_mode], None, cell_style_center),
            ('coa', 1, 0, 'text', _p.chart_account.name,
             None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style)
        return row_position

    def print_comparison_header(self, _xs, xlwt, row_position, _p, ws,
                                initial_balance_text):
        cell_format_ct = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
        cell_style_ct = xlwt.easyxf(cell_format_ct)
        c_specs = [('ct', 7, 0, 'text', _('Comparisons'))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, row_style=cell_style_ct)
        cell_format = _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style_center = xlwt.easyxf(cell_format)
        for index, params in enumerate(_p.comp_params):
            c_specs = [
                ('c', 2, 0, 'text', _('Comparison') + str(index + 1) +
                 ' (C' + str(index + 1) + ')')]
            if params['comparison_filter'] == 'filter_date':
                c_specs += [
                    ('f', 2, 0, 'text',
                     _('Dates Filter') + ': ' +
                     _p.formatLang(params['start'], date=True) + ' - ' +
                     _p.formatLang(params['stop'], date=True))]
            elif params['comparison_filter'] == 'filter_period':
                c_specs += [('f', 2, 0, 'text', _('Periods Filter') +
                             ': ' + params['start'].name + ' - ' +
                             params['stop'].name)]
            else:
                c_specs += [('f', 2, 0, 'text', _('Fiscal Year') +
                             ': ' + params['fiscalyear'].name)]
            c_specs += [('ib', 2, 0, 'text', _('Initial Balance') +
                         ': ' +
                         initial_balance_text[params['initial_balance_mode']])]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_position = self.xls_write_row(
                ws, row_position, row_data, row_style=cell_style_center)
        return row_position

    def print_account_header(self, ws, _p, _xs, xlwt, row_position):
        cell_format = _xs['bold'] + _xs['fill'] + \
            _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        if len(_p.comp_params) == 2:
            account_span = 3
        else:
            account_span = _p.initial_balance_mode and 2 or 3
        c_specs = [
            ('account', account_span, 0, 'text', _('Account / Partner Name')),
            ('code', 1, 0, 'text', _('Code / Ref')),
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
            ('acc_title', 7, 0, 'text', ' - '.join([current_account.code,
                                                    current_account.name])), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, cell_style)
        return row_position

    def print_account_totals(self, _xs, xlwt, ws, row_start_account,
                             row_position, current_account, _p):
        cell_format = _xs['bold'] + _xs['fill'] + \
            _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        c_specs = [
            ('acc_title', 2, 0, 'text', current_account.name),
            ('code', 1, 0, 'text', current_account.code),
        ]
        for column in range(3, 7):
            # in case of one single comparison, the column 6 will contain
            # percentages
            if (_p.comparison_mode == 'single' and column == 6):
                total_diff = rowcol_to_cell(row_position, column - 1)
                total_balance = rowcol_to_cell(row_position, column - 2)
                account_formula = 'Round(' + total_diff + \
                    '/' + total_balance + '*100;0)'
            else:
                account_start = rowcol_to_cell(row_start_account, column)
                account_end = rowcol_to_cell(row_position - 1, column)
                account_formula = 'Round(SUM(' + \
                    account_start + ':' + account_end + ');2)'
            c_specs += [('total%s' % column, 1, 0, 'text', None,
                         account_formula, None, cell_style_decimal)]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            ws, row_position, row_data, cell_style)
        return row_position + 1

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        # Initialisations
        ws = wb.add_sheet(_p.report_name[:31])
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

        initial_balance_text = {
            'initial_balance': _('Computed'),
            'opening_balance': _('Opening Entries'),
            False: _('No')}  # cf. account_report_partner_balance.mako
        # Print Header Table data
        row_pos = self.print_header_data(
            ws, _p, data, row_pos, xlwt, _xs, initial_balance_text)
        # Print comparison header table
        if _p.comparison_mode in ('single', 'multiple'):
            row_pos += 1
            row_pos = self.print_comparison_header(
                _xs, xlwt, row_pos, _p, ws, initial_balance_text)

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

            partners_order = _p['partners_order_accounts']\
                .get(current_account.id, False)

            # do not display accounts without partners
            if not partners_order:
                continue

            comparisons = _p['comparisons_accounts']\
                .get(current_account.id, False)

            # in multiple columns mode, we do not want to print accounts
            # without any rows
            if _p.comparison_mode in ('single', 'multiple'):
                all_comparison_lines = [comp['partners_amounts'][partner_id[1]]
                                        for partner_id in partners_order
                                        for comp in comparisons]
                if not display_line(all_comparison_lines):
                    continue

            current_partner_amounts = _p['partners_amounts_accounts']\
                .get(current_account.id, False)

            if _p.comparison_mode in ('single', 'multiple'):
                comparison_total = {}
                for i, comp in enumerate(comparisons):
                    comparison_total[i] = {'balance': 0.0}

            # print row: Code - Account name
            row_pos = self.print_row_code_account(
                ws, current_account, row_pos, _xs, xlwt)
            row_account_start = row_pos
            # Print row: Titles "Account/Partner Name-Code/ref-Initial
            # Balance-Debit-Credit-Balance" or  "Account/Partner
            # Name-Code/ref-Balance Year-Balance Year2-Balance C2-Balance C3"
            row_pos = self.print_account_header(ws, _p, _xs, xlwt, row_pos)

            for (partner_code_name, partner_id, partner_ref, partner_name) \
                    in partners_order:
                partner = current_partner_amounts.get(partner_id, {})
                # in single mode, we have to display all the partners even if
                # their balance is 0.0 because the initial balance should match
                # with the previous year closings
                # in multiple columns mode, we do not want to print partners
                # which have a balance at 0.0 in each comparison column
                if _p.comparison_mode in ('single', 'multiple'):
                    all_comparison_lines = [comp['partners_amounts']
                                            [partner_id]
                                            for comp in comparisons
                                            if comp['partners_amounts'].
                                            get(partner_id)]
                    if not display_line(all_comparison_lines):
                        continue

                # display data row
                if len(_p.comp_params) == 2:
                    account_span = 3
                else:
                    account_span = _p.initial_balance_mode and 2 or 3

                c_specs = [('acc_title', account_span, 0, 'text',
                            partner_name if partner_name else
                            _('Unallocated'))]
                c_specs += [('partner_ref', 1, 0, 'text',
                             partner_ref if partner_ref else '')]
                if _p.comparison_mode == 'no_comparison':
                    bal_formula = ''
                    if _p.initial_balance_mode:
                        init_bal_cell = rowcol_to_cell(row_pos, 3)
                        bal_formula = init_bal_cell + '+'
                        debit_col = 4
                        c_specs += [
                            ('init_bal', 1, 0, 'number', partner.get(
                                'init_balance', 0.0), None,
                             regular_cell_style_decimal),
                        ]
                    else:
                        debit_col = 3
                    c_specs += [
                        ('debit', 1, 0, 'number', partner.get('debit', 0.0),
                         None, regular_cell_style_decimal),
                        ('credit', 1, 0, 'number', partner.get('credit', 0.0),
                         None, regular_cell_style_decimal),
                    ]
                    debit_cell = rowcol_to_cell(row_pos, debit_col)
                    credit_cell = rowcol_to_cell(row_pos, debit_col + 1)
                    bal_formula += debit_cell + '-' + credit_cell
                    c_specs += [('bal', 1, 0, 'number', None,
                                 bal_formula, regular_cell_style_decimal), ]
                else:
                    c_specs += [('bal', 1, 0, 'number', partner.get('balance',
                                                                    0.0),
                                 None, regular_cell_style_decimal), ]

                if _p.comparison_mode in ('single', 'multiple'):
                    for i, comp in enumerate(comparisons):
                        comp_partners = comp['partners_amounts']
                        balance = diff = percent_diff = 0
                        if comp_partners.get(partner_id):
                            balance = comp_partners[partner_id]['balance']
                            diff = comp_partners[partner_id]['diff']
                            percent_diff = comp_partners[
                                partner_id]['percent_diff']
                            comparison_total[i]['balance'] += balance
                        c_specs += [('balance_%s' % i, 1, 0, 'number',
                                     balance, None,
                                     regular_cell_style_decimal), ]
                # no diff in multiple comparisons because it shows too much
                # data
                if _p.comparison_mode == 'single':
                    c_specs += [('balance_diff', 1, 0, 'number',
                                 diff, None, regular_cell_style_decimal), ]
                    if percent_diff is False:
                        c_specs += [('balance', 1, 0, 'number',
                                     diff, None, regular_cell_style_decimal), ]
                    else:
                        c_specs += [('perc_diff', 1, 0, 'number',
                                     int(round(percent_diff))), ]
                row_data = self.xls_row_template(
                    c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    ws, row_pos, row_data, regular_cell_style)

            row_pos = self.print_account_totals(
                _xs, xlwt, ws, row_account_start, row_pos, current_account, _p)


PartnersBalanceXls('report.account.account_report_partner_balance_xls',
                   'account.account',
                   parser=PartnerBalanceWebkit)
