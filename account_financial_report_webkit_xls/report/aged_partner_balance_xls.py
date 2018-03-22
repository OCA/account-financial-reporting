# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import xlwt
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report \
    .aged_partner_balance import AccountAgedTrialBalanceWebkit
from openerp.tools.translate import _
# import logging
# _logger = logging.getLogger(__name__)


class AccountAgedTrialBalanceWebkitXls(report_xls):

    # pylint: disable=old-api7-method-defined
    def create(self, cr, uid, ids, data, context=None):
        self._column_sizes = [
            30,  # Partner
            20,  # Partner Code
            20,  # Balance
            20,  # Due
            20,  # Overdue 0-30
            20,  # Overdue 30-60
            20,  # Overdue 60-90
            20,  # Overdue 90-120
            20,  # Overdue 120+
            ]
        self._balance_pos = 2
        return super(AccountAgedTrialBalanceWebkitXls, self).create(
            cr, uid, ids, data, context=context)

    def _cell_styles(self, _xs):
        self._style_title = xlwt.easyxf(_xs['xls_title'])
        self._style_bold_blue_center = xlwt.easyxf(
            _xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] +
            _xs['center'])
        self._style_center = xlwt.easyxf(
            _xs['borders_all'] + _xs['wrap'] + _xs['center'])

        format_yellow_bold = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self._style_account_title = xlwt.easyxf(
            format_yellow_bold + _xs['xls_title'])
        self._style_yellow_bold = xlwt.easyxf(format_yellow_bold)
        self._style_yellow_bold_right = xlwt.easyxf(
            format_yellow_bold + _xs['right'])
        self._style_yellow_bold_decimal = xlwt.easyxf(
            format_yellow_bold + _xs['right'],
            num_format_str=report_xls.decimal_format)

        self._style_default = xlwt.easyxf(_xs['borders_all'])
        self._style_decimal = xlwt.easyxf(
            _xs['borders_all'] + _xs['right'],
            num_format_str=report_xls.decimal_format)
        self._style_percent = xlwt.easyxf(
            _xs['borders_all'] + _xs['right'],
            num_format_str='0.00%')

    def _setup_worksheet(self, _p, _xs, data, wb):
        self.ws = wb.add_sheet(_p.report_name[:31])
        self.ws.panes_frozen = True
        self.ws.remove_splits = True
        self.ws.portrait = 0  # Landscape
        self.ws.fit_width_to_pages = 1
        self.ws.header_str = self.xls_headers['standard']
        self.ws.footer_str = self.xls_footers['standard']

    def _print_title(self, _p, _xs, data, row_pos):
        report_name = ' - '.join(
            [_p.report_name.upper(),
             _p.company.partner_id.name,
             _p.company.currency_id.name])
        c_specs = [
            ('report_name', 1, 0, 'text', report_name),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data, row_style=self._style_title)
        return row_pos

    def _print_empty_row(self, _p, _xs, data, row_pos):
        """
        Print empty row to define column sizes
        """
        c_specs = [('empty%s' % i, 1, self._column_sizes[i], 'text', None)
                   for i in range(len(self._column_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data, set_column_size=True)
        return row_pos

    def _print_header_title(self, _p, _xs, data, row_pos):
        c_specs = [
            ('coa', 1, 0, 'text', _('Chart of Account')),
            ('fy', 1, 0, 'text', _('Fiscal Year')),
            ('period_filter', 2, 0, 'text', _('Periods Filter')),
            ('cd', 1, 0, 'text', _('Clearance Date')),
            ('account_filter', 2, 0, 'text', _('Accounts Filter')),
            ('partner_filter', 1, 0, 'text', _('Partners Filter')),
            ('tm', 1, 0, 'text', _('Target Moves')),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data,
            row_style=self._style_bold_blue_center)
        return row_pos

    def _print_header_data(self, _p, _xs, data, row_pos):
        period_filter = _('From') + ': '
        period_filter += _p.start_period.name if _p.start_period else u''
        period_filter += ' ' + _('To') + ': '
        period_filter += _p.stop_period.name if _p.stop_period else u''
        c_specs = [
            ('coa', 1, 0, 'text', _p.chart_account.name),
            ('fy', 1, 0, 'text',
             _p.fiscalyear.name if _p.fiscalyear else '-'),
            ('period_filter', 2, 0, 'text', period_filter),
            ('cd', 1, 0, 'text', _p.date_until),
            ('account_filter', 2, 0, 'text',
             _p.display_partner_account(data)),
            ('partner_filter', 1, 0, 'text',
             _('Selected Partners') if _p.partner_ids else '-'),
            ('tm', 1, 0, 'text',
             _p.display_target_move(data)),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data, row_style=self._style_center)
        return row_pos

    def _print_header(self, _p, _xs, data, row_pos):
        """
        Header Table: Chart of Account, Fiscal year, Filters, ...
        """
        row_pos = self._print_header_title(_p, _xs, data, row_pos)
        row_pos = self._print_header_data(_p, _xs, data, row_pos)
        self.ws.set_horz_split_pos(row_pos)  # freeze the line
        return row_pos + 1

    def _print_account_header(self, _p, _xs, data, row_pos, account):
        """
        Fill in a row with the code and name of the account
        """
        c_specs = [
            ('acc_title', len(self._column_sizes), 0, 'text',
             ' - '.join([account.code, account.name])),
            ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data, self._style_account_title)
        return row_pos + 1

    def _print_partner_header(self, _p, _xs, data, row_pos):
        """
        Partner header line
        """
        c_specs = [
            ('partner_h', 1, 0, 'text', _('Partner'),
             None, self._style_yellow_bold),
            ('pcode_h', 1, 0, 'text', _('Code'),
             None, self._style_yellow_bold),
            ('balance_h', 1, 0, 'text', _('Balance')),
            ('due_h', 1, 0, 'text', _('Due'))]
        for days in [30, 60, 90, 120]:
            entry = 'od_%s_h' % days
            label = _("Overdue ≤ %s d.") % days
            c_specs += [(entry, 1, 0, 'text', label)]
        c_specs += [('older_h', 1, 0, 'text', _("Older"))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data,
            row_style=self._style_yellow_bold_right)
        return row_pos

    def _print_partner_line(self, _p, _xs, data, row_pos, partner, line):
        """
        Partner data line
        """
        partner_name, p_id, p_ref, p_name = partner
        c_specs = [
            ('partner', 1, 0, 'text', p_name,
             None, self._style_default),
            ('pcode', 1, 0, 'text', p_ref,
             None, self._style_default),
            ('balance', 1, 0, 'number', line['balance'])]
        for r in _p.ranges:
            entry = 'od_%s' % r[0]
            c_specs += [(entry, 1, 0, 'number', line['aged_lines'][r])]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data,
            row_style=self._style_decimal)
        return row_pos

    def _print_partner_footer(self, _p, _xs, data, row_pos,
                              account, line_count):
        """
        Partner header line
        """
        # Totals
        c_specs = [
            ('total', 1, 0, 'text', _('Total') + ' ' + account.code,
             None, self._style_yellow_bold),
            ('empty', 1, 0, 'text', None,
             None, self._style_yellow_bold)]
        row_start = row_pos - line_count
        col_start = self._balance_pos
        start = rowcol_to_cell(row_start, col_start)
        stop = rowcol_to_cell(row_pos - 1, col_start)
        formula = 'SUM(%s:%s)' % (start, stop)
        c_specs += [('total_balance', 1, 0, 'number', None, formula)]
        col_start += 1
        for i, r in enumerate(_p.ranges):
            entry = 'total_%s' % i
            start = rowcol_to_cell(row_start, col_start + i)
            stop = rowcol_to_cell(row_pos - 1, col_start + i)
            formula = 'SUM(%s:%s)' % (start, stop)
            c_specs += [(entry, 1, 0, 'number', None, formula)]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data,
            row_style=self._style_yellow_bold_decimal)

        # percents
        c_specs = [
            ('pct', 1, 0, 'text', _('Percentages') + ' ' + account.code,
             None, self._style_default),
            ('empty', 2, 0, 'text', None,
             None, self._style_default)]
        total_balance = rowcol_to_cell(row_pos - 1, self._balance_pos)
        for i, r in enumerate(_p.ranges):
            entry = 'pct_%s' % i
            total_range = rowcol_to_cell(row_pos - 1, col_start + i)
            formula = '%s/%s' % (total_range, total_balance)
            c_specs += [(entry, 1, 0, 'number', None, formula)]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            self.ws, row_pos, row_data,
            row_style=self._style_percent)

        return row_pos

    def _print_account_data(self, _p, _xs, data, row_pos, account):
        if _p.agged_lines_accounts.get(account.id):
            row_pos = self._print_account_header(
                _p, _xs, data, row_pos, account)
            lines = _p.agged_lines_accounts[account.id]

            row_pos = self._print_partner_header(
                _p, _xs, data, row_pos)
            row_pos_start = row_pos
            for partner in _p.partners_order[account.id]:
                partner_id = partner[1]
                if partner_id in lines:
                    line = lines[partner_id]
                    row_pos = self._print_partner_line(
                        _p, _xs, data, row_pos, partner, line)
            line_count = row_pos - row_pos_start
            row_pos = self._print_partner_footer(
                _p, _xs, data, row_pos, account, line_count)
        return row_pos + 1

    def generate_xls_report(self, _p, _xs, data, objects, wb):

        self._cell_styles(_xs)
        self._setup_worksheet(_p, _xs, data, wb)

        row_pos = 0
        row_pos = self._print_title(_p, _xs, data, row_pos)
        row_pos = self._print_empty_row(_p, _xs, data, row_pos)
        row_pos = self._print_header(_p, _xs, data, row_pos)

        for account in objects:
            row_pos = self._print_account_data(
                _p, _xs, data, row_pos, account)


AccountAgedTrialBalanceWebkitXls(
    'report.account.account_report_aged_partner_balance_xls',
    'account.account',
    parser=AccountAgedTrialBalanceWebkit)
