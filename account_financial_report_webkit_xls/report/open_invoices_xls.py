# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import xlwt
from datetime import datetime
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.open_invoices \
    import PartnersOpenInvoicesWebkit
from openerp.tools.translate import _
# import logging
# _logger = logging.getLogger(__name__)


class OpenInvoicesXls(report_xls):
    column_sizes = [12, 12, 20, 15, 30, 30, 14, 14, 14, 14, 14, 14, 10]

    def global_initializations(self, wb, _p, xlwt, _xs, objects, data):
        # this procedure will initialise variables and Excel cell styles and
        # return them as global ones
        self.ws = wb.add_sheet(_p.report_name[:31])
        self.ws.panes_frozen = True
        self.ws.remove_splits = True
        self.ws.portrait = 0  # Landscape
        self.ws.fit_width_to_pages = 1
        self.ws.header_str = self.xls_headers['standard']
        self.ws.footer_str = self.xls_footers['standard']
        # -------------------------------------------------------
        # number of columns is 11 in case of normal report, 13 in case the
        # option currency is selected and 12 in case of the regroup by currency
        # option is checked
        group_lines = False
        # search if the regroup option is selected by browsing the accounts
        # defined in objects - see account_report_open_invoices.mako
        for acc in objects:
            if hasattr(acc, 'grouped_ledger_lines'):
                group_lines = True
        if group_lines:
            self.nbr_columns = 12
        elif _p.amount_currency(data) and not group_lines:
            self.nbr_columns = 13
        else:
            self.nbr_columns = 11
        # -------------------------------------------------------
        # cell style for report title
        self.style_font12 = xlwt.easyxf(_xs['xls_title'])
        # -------------------------------------------------------
        self.style_default = xlwt.easyxf(_xs['borders_all'])
        # -------------------------------------------------------
        self.style_default_italic = xlwt.easyxf(
            _xs['borders_all'] + _xs['italic'])
        # -------------------------------------------------------
        self.style_bold = xlwt.easyxf(_xs['bold'] + _xs['borders_all'])
        # -------------------------------------------------------
        # cell style for header titles: 'Chart of accounts' - 'Fiscal year' ...
        self.style_bold_blue_center = xlwt.easyxf(
            _xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] +
            _xs['center'])
        # -------------------------------------------------------
        # cell style for header data: 'Chart of accounts' - 'Fiscal year' ...
        self.style_center = xlwt.easyxf(
            _xs['borders_all'] + _xs['wrap'] + _xs['center'])
        # -------------------------------------------------------
        # cell style for columns titles 'Date'- 'Period' - 'Entry'...
        self.style_yellow_bold = xlwt.easyxf(
            _xs['bold'] + _xs['fill'] + _xs['borders_all'])
        # -------------------------------------------------------
        # cell style for columns titles 'Date'- 'Period' - 'Entry'...
        self.style_yellow_bold_right = xlwt.easyxf(
            _xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['right'])
        # -------------------------------------------------------
        self.style_right = xlwt.easyxf(_xs['borders_all'] + _xs['right'])
        # -------------------------------------------------------
        self.style_right_italic = xlwt.easyxf(
            _xs['borders_all'] + _xs['right'] + _xs['italic'])
        # -------------------------------------------------------
        self.style_decimal = xlwt.easyxf(
            _xs['borders_all'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        # -------------------------------------------------------
        self.style_decimal_italic = xlwt.easyxf(
            _xs['borders_all'] + _xs['right'] + _xs['italic'],
            num_format_str=report_xls.decimal_format)
        # -------------------------------------------------------
        self.style_date = xlwt.easyxf(
            _xs['borders_all'] + _xs['left'],
            num_format_str=report_xls.date_format)
        # -------------------------------------------------------
        self.style_date_italic = xlwt.easyxf(
            _xs['borders_all'] + _xs['left'] + _xs['italic'],
            num_format_str=report_xls.date_format)
        # -------------------------------------------------------
        cell_format = _xs['xls_title'] + _xs['bold'] + \
            _xs['fill'] + _xs['borders_all']
        self.style_account_title = xlwt.easyxf(cell_format)
        self.style_account_title_right = xlwt.easyxf(
            cell_format + _xs['right'])
        self.style_account_title_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        # -------------------------------------------------------
        cell_format = _xs['bold']
        self.style_partner_row = xlwt.easyxf(cell_format)
        # -------------------------------------------------------
        cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.style_partner_cumul = xlwt.easyxf(cell_format)
        self.style_partner_cumul_right = xlwt.easyxf(
            cell_format + _xs['right'])
        self.style_partner_cumul_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

    # print the first line "OPEN INVOICE REPORT - db name - Currency
    def print_title(self, _p, row_position):
        report_name = ' - '.join([_p.report_name.upper(),
                                 _p.company.partner_id.name,
                                 _p.company.currency_id.name])
        c_specs = [('report_name', self.nbr_columns, 0, 'text', report_name), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, row_style=self.style_font12)
        return row_position

    # send an empty row to the Excel document
    def print_empty_row(self, row_position):
        c_sizes = self.column_sizes
        c_specs = [('empty%s' % i, 1, c_sizes[i], 'text', None)
                   for i in range(0, len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, set_column_size=True)
        return row_position

    # Fill in the titles of the header summary tables: Chart of account -
    # Fiscal year - ...
    def print_header_titles(self, _p, data, row_position):
        c_specs = [
            ('coa', 2, 0, 'text', _('Chart of Account'),
             None, self.style_bold_blue_center),
            ('fy', 2, 0, 'text', _('Fiscal Year'),
             None, self.style_bold_blue_center),
            ('df', 2, 0, 'text', _p.filter_form(data) == 'filter_date' and _(
                'Dates Filter') or _('Periods Filter'), None,
             self.style_bold_blue_center),
            ('cd', 1 if self.nbr_columns == 11 else 2, 0, 'text',
             _('Clearance Date'), None, self.style_bold_blue_center),
            ('af', 2, 0, 'text', _('Accounts Filter'),
             None, self.style_bold_blue_center),
            ('tm', 3 if self.nbr_columns == 13 else 2, 0, 'text',
             _('Target Moves'), None, self.style_bold_blue_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data,
            row_style=self.style_bold_blue_center)
        return row_position

    # Fill in the data of the header summary tables: Chart of account - Fiscal
    # year - ...
    def print_header_data(self, _p, data, row_position):
        c_specs = [
            ('coa', 2, 0, 'text', _p.chart_account.name,
             None, self.style_center),
            ('fy', 2, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-',
             None, self.style_center),
        ]
        df = _('From') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.start_date if _p.start_date else u''
        else:
            df += _p.start_period.name if _p.start_period else u''
        df += ' ' + _('To') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.stop_date if _p.stop_date else u''
        else:
            df += _p.stop_period.name if _p.stop_period else u''
        c_specs += [
            ('df', 2, 0, 'text', df, None, self.style_center),
            ('cd', 1 if self.nbr_columns == 11 else 2, 0, 'text',
             _p.date_until, None, self.style_center),  # clearance date
            ('af', 2, 0, 'text', _('Custom Filter')
             if _p.partner_ids else _p.display_partner_account(data), None,
             self.style_center),
            ('tm', 3 if self.nbr_columns == 13 else 2, 0, 'text',
             _p.display_target_move(data), None, self.style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, row_style=self.style_center)
        return row_position

    # Fill in a row with the titles of the columns for the invoice lines: Date
    # - Period - Entry -...
    def print_columns_title(self, _p, row_position, data, group_lines=False):
        c_specs = [
            ('date', 1, 0, 'text', _('Date'), None, self.style_yellow_bold),
            ('period', 1, 0, 'text', _('Period'),
             None, self.style_yellow_bold),
            ('entry', 1, 0, 'text', _('Entry'), None, self.style_yellow_bold),
            ('journal', 1, 0, 'text', _('Journal'),
             None, self.style_yellow_bold),
        ]
        if not group_lines:
            c_specs += [('partner', 1, 0, 'text', _('Partner'),
                         None, self.style_yellow_bold), ]
        c_specs += [
            ('label', 1, 0, 'text', _('Label'), None, self.style_yellow_bold),
            ('rec', 1, 0, 'text', _('Rec.'), None, self.style_yellow_bold),
            ('due_date', 1, 0, 'text', _('Due Date'),
             None, self.style_yellow_bold),
            ('debit', 1, 0, 'text', _('Debit'),
             None, self.style_yellow_bold_right),
            ('credit', 1, 0, 'text', _('Credit'),
             None, self.style_yellow_bold_right),
            ('cumul', 1, 0, 'text', _('Cumul. Bal.'),
             None, self.style_yellow_bold_right),
        ]
        if group_lines:
            c_specs += [
                ('currbal', 1, 0, 'text', _('Curr. Balance'),
                 None, self.style_yellow_bold_right),
                ('curr', 1, 0, 'text', _('Curr.'),
                 None, self.style_yellow_bold_right),
            ]
        else:
            if _p.amount_currency(data):
                c_specs += [
                    ('currbal', 1, 0, 'text', _('Curr. Balance'),
                     None, self.style_yellow_bold_right),
                    ('curr', 1, 0, 'text', _('Curr.'),
                     None, self.style_yellow_bold_right),
                ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, row_style=self.style_yellow_bold)
        return row_position

    # Fill in a row with the code and the name of an account + the partner
    # name in case of currency regrouping
    def print_row_code_account(self, regroupmode, account, row_position,
                               partner_name):
        if regroupmode == "regroup":
            c_specs = [('acc_title', self.nbr_columns, 0, 'text',
                        ' - '.join([account.code,
                                    account.name,
                                    partner_name or _('No partner')])), ]
        else:
            c_specs = [
                ('acc_title', self.nbr_columns, 0, 'text', ' - '.
                 join([account.code, account.name])), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_account_title)
        return row_position + 1

    def print_row_partner(self, row_position, partner_name):
        c_specs = [
            ('partner', self.nbr_columns, 0, 'text',
             partner_name or _('No partner')), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_partner_row)
        return row_position

    def print_group_currency(self, row_position, curr, _p):
        c_specs = [
            ('curr', self.nbr_columns, 0, 'text',
             curr or _p.company.currency_id.name), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_bold)
        return row_position

    # Fill in rows of invoice line
    def print_lines(self, row_position, account, line, _p, data, line_number):

        label_elements = [line.get('lname') or '']
        if line.get('invoice_number'):
            label_elements.append("(%s)" % (line['invoice_number'],))
        label = ' '.join(label_elements)

        # Mako: <div class="act_as_row lines
        # ${line.get('is_from_previous_periods') and
        # 'open_invoice_previous_line' or ''} ${line.get('is_clearance_line')
        # and 'clearance_line' or ''}">
        if line.get('is_from_previous_periods') \
                or line.get('is_clearance_line'):
            style_line_default = self.style_default_italic
            style_line_right = self.style_right_italic
            style_line_date = self.style_date_italic
            style_line_decimal = self.style_decimal_italic
        else:
            style_line_default = self.style_default
            style_line_right = self.style_right
            style_line_date = self.style_date
            style_line_decimal = self.style_decimal
        if line.get('ldate'):
            c_specs = [('date', 1, 0, 'date', datetime.strptime(
                line['ldate'], '%Y-%m-%d'), None, style_line_date)]
        else:
            c_specs = [('date', 1, 0, 'text', None)]
        c_specs += [
            ('period_code', 1, 0, 'text', line.get('period_code') or ''),
            ('entry', 1, 0, 'text', line.get('move_name') or ''),
            ('journal', 1, 0, 'text', line.get('jcode') or ''),
            ('partner', 1, 0, 'text', line.get('partner_name') or ''),
            ('label', 1, 0, 'text', label),
            ('rec', 1, 0, 'text', line.get('rec_name') or ''),
        ]
        if line.get('date_maturity'):
            c_specs += [('datedue', 1, 0, 'date',
                         datetime.strptime(line['date_maturity'], '%Y-%m-%d'),
                         None, style_line_date)]
        else:
            c_specs += [('datedue', 1, 0, 'text', None)]
        c_specs += [
            ('debit', 1, 0, 'number', line.get('debit') or 0.0, None,
             style_line_decimal),
            ('credit', 1, 0, 'number', line.get('credit') or 0.0, None,
             style_line_decimal),
        ]

        # determine the formula of the cumulated balance
        debit_cell = rowcol_to_cell(row_position, 8)
        credit_cell = rowcol_to_cell(row_position, 9)
        previous_balance = rowcol_to_cell(row_position - 1, 10)

        # if it is the first line, the balance is only debit - credit
        if line_number == 1:
            cumul_balance = debit_cell + '-' + credit_cell
        # cumulate debit - credit and balance of previous line
        else:
            cumul_balance = debit_cell + '-' + \
                credit_cell + '+' + previous_balance

        c_specs += [('cumul', 1, 0, 'number', None,
                     cumul_balance, style_line_decimal)]

        if _p.amount_currency(data):
            if line.get('currency_code'):
                c_specs += [
                    ('curramount', 1, 0, 'number',
                     line.get('amount_currency') or 0.0, None,
                     style_line_decimal),
                    ('currcode', 1, 0, 'text', line[
                     'currency_code'], None, style_line_right),
                ]
            else:
                c_specs += [
                    ('curramount', 1, 0, 'text', '-', None, style_line_right),
                    ('currcode', 1, 0, 'text', '', None, style_line_right),
                ]

        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, style_line_default)
        return row_position

    # Fill in rows of invoice line when the option currency regroup is
    # selecself.wsd
    def print_group_lines(self, row_position, account, line, _p, line_number):

        label_elements = [line.get('lname') or '']
        if line.get('invoice_number'):
            label_elements.append("(%s)" % (line['invoice_number'],))
        label = ' '.join(label_elements)
        # Mako: <div class="act_as_row lines
        # ${line.get('is_from_previous_periods') and
        # 'open_invoice_previous_line' or ''} ${line.get('is_clearance_line')
        # and 'clearance_line' or ''}">
        if line.get('is_from_previous_periods') or \
                line.get('is_clearance_line'):
            style_line_default = self.style_default_italic
            style_line_right = self.style_right_italic
            style_line_date = self.style_date_italic
            style_line_decimal = self.style_decimal_italic
        else:
            style_line_default = self.style_default
            style_line_right = self.style_right
            style_line_date = self.style_date
            style_line_decimal = self.style_decimal

        debit_cell = rowcol_to_cell(row_position, 7)
        credit_cell = rowcol_to_cell(row_position, 8)
        previous_balance = rowcol_to_cell(row_position - 1, 9)

        # if it is the first line, the balance is only debit - credit
        if line_number == 1:
            cumul_balance = debit_cell + '-' + credit_cell
        # cumulate devit - credit and balance of previous line
        else:
            cumul_balance = debit_cell + '-' + \
                credit_cell + '+' + previous_balance

        if line.get('ldate'):
            c_specs = [('date', 1, 0, 'date', datetime.strptime(
                line['ldate'], '%Y-%m-%d'), None, style_line_date)]
        else:
            c_specs = [('date', 1, 0, 'text', None)]
        c_specs += [
            ('period_code', 1, 0, 'text', line.get('period_code') or ''),
            ('entry', 1, 0, 'text', line.get('move_name') or ''),
            ('journal', 1, 0, 'text', line.get('jcode') or ''),
            ('label', 1, 0, 'text', label),
            ('rec', 1, 0, 'text', line.get('rec_name') or ''),
        ]
        if line.get('date_maturity'):
            c_specs += [('datedue', 1, 0, 'date',
                         datetime.strptime(line['date_maturity'], '%Y-%m-%d'),
                         None, style_line_date)]
        else:
            c_specs += [('datedue', 1, 0, 'text', None)]
        c_specs += [
            ('debit', 1, 0, 'number', line.get('debit') or 0.0, None,
             style_line_decimal),
            ('credit', 1, 0, 'number', line.get('credit') or 0.0, None,
             style_line_decimal),
            ('cumul', 1, 0, 'number', None, cumul_balance, style_line_decimal),
        ]
        if account.currency_id:
            c_specs += [
                ('curramount', 1, 0, 'number',
                 line.get('amount_currency') or 0.0, None, style_line_decimal),
                ('currcode', 1, 0, 'text',
                 line.get('currency_code') or '', None, style_line_right),
            ]
        else:
            c_specs += [
                ('curramount', 1, 0, 'text', '-', None, style_line_right),
                ('currcode', 1, 0, 'text', '', None, style_line_right),
            ]

        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, style_line_default)
        return (row_position, cumul_balance)

    # print by partner the totals and cumulated balance (Excel formulas)
    def print_cumul_partner(self, row_position, row_start_partner, account, _p,
                            data):

        # the text "Cumulated Balance on Partner starts in column 4 when
        # selecting the option regroup by currency, 5 in  the other case
        start_col = 5

        debit_partner_start = rowcol_to_cell(row_start_partner, start_col + 3)
        debit_partner_end = rowcol_to_cell(row_position - 1, start_col + 3)
        debit_partner_total = 'SUM(' + debit_partner_start + \
            ':' + debit_partner_end + ')'

        credit_partner_start = rowcol_to_cell(row_start_partner, start_col + 4)
        credit_partner_end = rowcol_to_cell(row_position - 1, start_col + 4)
        credit_partner_total = 'SUM(' + credit_partner_start + \
            ':' + credit_partner_end + ')'

        bal_curr_start = rowcol_to_cell(row_start_partner, start_col + 6)
        bal_curr_end = rowcol_to_cell(row_position - 1, start_col + 6)
        cumul_balance_curr = 'SUM(' + bal_curr_start + ':' + bal_curr_end + ')'

        bal_partner_debit = rowcol_to_cell(row_position, start_col + 3)
        bal_partner_credit = rowcol_to_cell(row_position, start_col + 4)
        bal_partner_total = bal_partner_debit + '-' + bal_partner_credit

        c_specs = [('empty%s' % x, 1, 0, 'text', None)
                   for x in range(start_col)]

        c_specs += [
            ('init_bal', 1, 0, 'text', _('Cumulated Balance on Partner')),
            ('rec', 1, 0, 'text', None),
            ('empty5', 1, 0, 'text', None),
            ('debit', 1, 0, 'number', None,
             debit_partner_total, self.style_partner_cumul_decimal),
            ('credit', 1, 0, 'number', None,
             credit_partner_total, self.style_partner_cumul_decimal),
            ('cumul_bal', 1, 0, 'number', None,
             bal_partner_total, self.style_partner_cumul_decimal),
        ]
        if _p.amount_currency(data):
            if account.currency_id:
                c_specs += [('cumul_bal_curr', 1, 0, 'number', None,
                             cumul_balance_curr,
                             self.style_partner_cumul_decimal),
                            ('curr_name', 1, 0, 'text',
                             account.currency_id.name,
                             None, self.style_partner_cumul_right),
                            ]
            else:
                c_specs += [('cumul_bal_curr', 1, 0, 'text', '-', None,
                             self.style_partner_cumul_right),
                            ('curr_name', 1, 0, 'text', '',
                             None, self.style_partner_cumul_right)
                            ]

        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_partner_cumul)
        return row_position + 1

    # print by partner the totals and cumulated balance (Excel formulas) when
    # the option currency regroup is selected
    def print_group_cumul_partner(self, row_position, row_start_partner,
                                  account, _p, data):

        # the text "Cumulated Balance on Partner starts in column 4 when
        # selecting the option regroup by currency, 5 in  the other case
        start_col = 4

        debit_partner_start = rowcol_to_cell(row_start_partner, start_col + 3)
        debit_partner_end = rowcol_to_cell(row_position - 1, start_col + 3)
        debit_partner_total = 'SUM(' + debit_partner_start + \
            ':' + debit_partner_end + ')'

        credit_partner_start = rowcol_to_cell(row_start_partner, start_col + 4)
        credit_partner_end = rowcol_to_cell(row_position - 1, start_col + 4)
        credit_partner_total = 'SUM(' + credit_partner_start + \
            ':' + credit_partner_end + ')'

        bal_curr_start = rowcol_to_cell(row_start_partner, start_col + 5)
        bal_curr_end = rowcol_to_cell(row_position - 1, start_col + 5)
        cumul_balance_curr = 'SUM(' + bal_curr_start + ':' + bal_curr_end + ')'

        bal_partner_debit = rowcol_to_cell(row_position, start_col + 3)
        bal_partner_credit = rowcol_to_cell(row_position, start_col + 4)
        bal_partner_total = bal_partner_debit + '-' + bal_partner_credit

        c_specs = [('empty%s' % x, 1, 0, 'text', None)
                   for x in range(start_col)]

        c_specs += [
            # , style_bold_italic),
            ('init_bal', 1, 0, 'text', _('Cumulated Balance on Partner')),
            ('rec', 1, 0, 'text', None),
            ('empty5', 1, 0, 'text', None),
            ('debit', 1, 0, 'number', None,
             debit_partner_total, self.style_partner_cumul_decimal),
            ('credit', 1, 0, 'number', None,
             credit_partner_total, self.style_partner_cumul_decimal),
            ('cumul_bal', 1, 0, 'number', None,
             bal_partner_total, self.style_partner_cumul_decimal),
        ]
        if account.currency_id:
            c_specs += [
                ('cumul_bal_curr', 1, 0, 'number', None,
                 cumul_balance_curr, self.style_partner_cumul_decimal),
                ('curr_name', 1, 0, 'text', account.currency_id.name,
                 None, self.style_partner_cumul_right),
            ]
        else:
            c_specs += [
                ('cumul_bal_curr', 1, 0, 'text', "-",
                 None, self.style_partner_cumul_right),
                ('curr_name', 1, 0, 'text', "",
                 None, self.style_partner_cumul_right),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_partner_cumul)
        return row_position + 1

    # print by account the totals of the credit and debit + balance calculation
    def print_cumul_account(self, row_position, row_start_account, account, _p,
                            data):

        # This procedure will create  an Excel sumif function that will check
        # in the column "label" for the "Cumulated Balance.." string and make a
        # sum of the debit & credit data
        # the text "Cumulated Balance on Partner starts in column 4 when
        # selecting the option regroup by currency, 5 in  the other case
        start_col = 5

        # range in which we search for the text "Cumulated Balance on Partner"
        reference_start = rowcol_to_cell(row_start_account, start_col)
        reference_stop = rowcol_to_cell(row_position - 1, start_col)

        # range in which we make the sum of all the cumulated balance lines
        # (debit)
        range_debit_start = rowcol_to_cell(row_start_account, start_col + 3)
        range_debit_stop = rowcol_to_cell(row_position - 1, start_col + 3)

        # range in which we make the sum of all the cumulated balance lines
        # (crebit)
        range_credit_start = rowcol_to_cell(row_start_account, start_col + 4)
        range_credit_stop = rowcol_to_cell(row_position - 1, start_col + 4)

        search_key = _('Cumulated Balance on Partner')
        total_debit_account = 'SUMIF(' + reference_start + ':' + \
            reference_stop + ';"' + search_key + '";' + range_debit_start + \
            ':' + range_debit_stop + ')'
        total_credit_account = 'SUMIF(' + reference_start + ':' + \
            reference_stop + ';"' + search_key + '";' + range_credit_start + \
            ':' + range_credit_stop + ')'

        bal_account_debit = rowcol_to_cell(row_position, start_col + 3)
        bal_account_credit = rowcol_to_cell(row_position, start_col + 4)
        bal_account_total = bal_account_debit + '-' + bal_account_credit

        bal_curr_start = rowcol_to_cell(row_start_account, start_col + 6)
        bal_curr_end = rowcol_to_cell(row_position - 1, start_col + 6)
        cumul_balance_curr = 'SUMIF(' + reference_start + ':' + \
            reference_stop + ';"' + search_key + '";' + \
            bal_curr_start + ':' + bal_curr_end + ')'

        c_specs = [
            ('acc_title', start_col, 0, 'text',
             ' - '.join([account.code, account.name])),
            ('init_bal', 2, 0, 'text',
             _('Cumulated Balance on Account')),
            ('empty2', 1, 0, 'text', None),
            ('debit', 1, 0, 'number', None,
             total_debit_account, self.style_account_title_decimal),
            ('credit', 1, 0, 'number', None,
             total_credit_account, self.style_account_title_decimal),
            ('balance', 1, 0, 'number', None,
             bal_account_total, self.style_account_title_decimal),
        ]
        if _p.amount_currency(data):
            if account.currency_id:
                c_specs += [('cumul_bal_curr', 1, 0, 'number', None,
                             cumul_balance_curr),
                            ('curr_name', 1, 0, 'text',
                             account.currency_id.name,
                             None, self.style_account_title_right),
                            ]
            else:
                c_specs += [('cumul_bal_curr', 1, 0, 'text', "-", None,
                             self.style_account_title_right),
                            ('curr_name', 1, 0, 'text', "",
                             None, self.style_account_title_right)
                            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_account_title)
        return row_position + 1

    # print by account the totals of the credit and debit + balance calculation
    def print_group_cumul_account(self, row_position, row_start_account,
                                  account):
        # This procedure will create  an Excel sumif function that will check
        # in the column "label" for the "Cumulated Balance.." string and make a
        # sum of the debit & credit data
        # the text "Cumulated Balance on Partner starts in column 4 when
        # selecting the option regroup by currency, 5 in  the other case
        start_col = 4

        # range in which we search for the text "Cumulated Balance on Partner"
        reference_start = rowcol_to_cell(row_start_account, start_col)
        reference_stop = rowcol_to_cell(row_position - 1, start_col)

        # range in which we make the sum of all the cumulated balance lines
        # (debit)
        range_debit_start = rowcol_to_cell(row_start_account, start_col + 3)
        range_debit_stop = rowcol_to_cell(row_position - 1, start_col + 3)

        # range in which we make the sum of all the cumulated balance lines
        # (crebit)
        range_credit_start = rowcol_to_cell(row_start_account, start_col + 4)
        range_credit_stop = rowcol_to_cell(row_position - 1, start_col + 4)

        search_key = _('Cumulated Balance on Partner')
        total_debit_account = 'SUMIF(' + reference_start + ':' + \
            reference_stop + ';"' + search_key + '";' + range_debit_start + \
            ':' + range_debit_stop + ')'
        total_credit_account = 'SUMIF(' + reference_start + ':' + \
            reference_stop + ';"' + search_key + '";' + range_credit_start + \
            ':' + range_credit_stop + ')'

        bal_account_debit = rowcol_to_cell(row_position, start_col + 3)
        bal_account_credit = rowcol_to_cell(row_position, start_col + 4)
        bal_account_total = bal_account_debit + '-' + bal_account_credit

        bal_curr_start = rowcol_to_cell(row_start_account, start_col + 6)
        bal_curr_end = rowcol_to_cell(row_position - 1, start_col + 6)
        cumul_balance_curr = 'SUMIF(' + reference_start + ':' + \
            reference_stop + ';"' + search_key + '";' + \
            bal_curr_start + ':' + bal_curr_end + ')'

        c_specs = [
            ('acc_title', start_col, 0, 'text',
             ' - '.join([account.code, account.name])),
            ('init_bal', 2, 0, 'text',
             _('Cumulated Balance on Account')),
            ('empty2', 1, 0, 'text', None),
            ('debit', 1, 0, 'number', None,
             total_debit_account, self.style_account_title_decimal),
            ('credit', 1, 0, 'number', None,
             total_credit_account, self.style_account_title_decimal),
            ('balance', 1, 0, 'number', None,
             bal_account_total, self.style_account_title_decimal),
        ]
        if account.currency_id:
            c_specs += [('cumul_bal_curr', 1, 0, 'number', None,
                         cumul_balance_curr, self.style_account_title_decimal),
                        ('curr_name', 1, 0, 'text', account.currency_id.name,
                         None, self.style_account_title_decimal),
                        ]
        else:
            c_specs += [('cumul_bal_curr', 1, 0, 'text', "-", None,
                         self.style_account_title_right),
                        ('curr_name', 1, 0, 'text', "",
                         None, self.style_account_title_right)
                        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(
            self.ws, row_position, row_data, self.style_account_title)
        return row_position + 1

    # export the invoice AR/AP lines when the option currency regroup is
    # selected
    def print_grouped_line_report(self, row_pos, account, _xs, xlwt, _p, data):

        if account.grouped_ledger_lines and \
           _p['partners_order'][account.id]:
            row_start_account = row_pos

            for partner_name, p_id, p_ref, p_name \
                    in _p['partners_order'][account.id]:
                row_pos = self.print_row_code_account(
                    "regroup", account, row_pos, partner_name)

                for curr, grouped_lines in account.grouped_ledger_lines.\
                        get(p_id, []):

                    row_pos = self.print_group_currency(row_pos, curr, _p)
                    # Print row: Titles "Date-Period-Entry-Journal..."
                    row_pos = self.print_columns_title(
                        _p, row_pos, data, group_lines=True)

                    row_pos_start = row_pos
                    line_number = 0
                    for line in grouped_lines:
                        line_number += 1
                        row_pos, cumul_balance = self.print_group_lines(
                            row_pos, account, line, _p, line_number)
                    row_pos = self.print_group_cumul_partner(
                        row_pos, row_pos_start, account, _p, data)

            row_pos = self.print_group_cumul_account(
                row_pos, row_start_account, account)

        return row_pos

    # export the invoice AR/AP lines
    def print_ledger_lines(self, row_pos, account, _xs, xlwt, _p, data):

        if _p['ledger_lines'][account.id] \
           and _p['partners_order'][account.id]:

            row_start_account = row_pos

            # Print account line: code - account
            row_pos = self.print_row_code_account(
                "noregroup", account, row_pos, "")
            for partner_name, p_id, p_ref, p_name \
                    in _p['partners_order'][account.id]:

                # Print partner row
                row_pos = self.print_row_partner(row_pos, partner_name)
                # Print row: Titles "Date-Period-Entry-Journal..."
                row_pos = self.print_columns_title(
                    _p, row_pos, data, group_lines=False)

                row_pos_start = row_pos
                line_number = 0
                for line in _p['ledger_lines'][account.id].get(p_id, []):
                    line_number += 1
                    # print ledger lines
                    row_pos = self.print_lines(
                        row_pos, account, line, _p, data, line_number)
                row_pos = self.print_cumul_partner(
                    row_pos, row_pos_start, account, _p, data)

            row_pos = self.print_cumul_account(
                row_pos, row_start_account, account, _p, data)

        return row_pos

    def generate_xls_report(self, _p, _xs, data, objects, wb):  # main function

        # Initializations
        self.global_initializations(wb, _p, xlwt, _xs, objects, data)
        row_pos = 0
        # Print Title
        row_pos = self.print_title(_p, row_pos)
        # Print empty row to define column sizes
        row_pos = self.print_empty_row(row_pos)
        # Print Header Table titles (Fiscal Year - Accounts Filter - Periods
        # Filter...)
        row_pos = self.print_header_titles(_p, data, row_pos)
        # Print Header Table data
        row_pos = self.print_header_data(_p, data, row_pos)
        # Freeze the line
        self.ws.set_horz_split_pos(row_pos)
        # Print empty row
        row_pos = self.print_empty_row(row_pos)

        for acc in objects:
            if hasattr(acc, 'grouped_ledger_lines'):
                # call xls equivalent of
                # "grouped_by_curr_open_invoices_inclusion.mako.html"
                row_pos = self.print_grouped_line_report(
                    row_pos, acc, _xs, xlwt, _p, data)
            else:
                # call xls equivalent of "open_invoices_inclusion.mako.html"
                row_pos = self.print_ledger_lines(
                    row_pos, acc, _xs, xlwt, _p, data)
            row_pos += 1


OpenInvoicesXls('report.account.account_report_open_invoices_xls',
                'account.account', parser=PartnersOpenInvoicesWebkit)
