# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# Copyright 2018 Jacques-Etienne Baudoux (BCIM sprl) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from datetime import datetime
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.addons.account_financial_report_webkit.report.general_ledger \
    import GeneralLedgerWebkit
from openerp.tools.translate import _


def cell(row, col, row_abs=False, col_abs=False):
    """
    Convert numeric row/col notation to an Excel cell
    reference string in A1 notation.
    """
    d = col // 26
    m = col % 26
    chr1 = ""    # Most significant character in AA1
    if row_abs:
        row_abs = '$'
    else:
        row_abs = ''
    if col_abs:
        col_abs = '$'
    else:
        col_abs = ''
    if d > 0:
        chr1 = chr(ord('A') + d - 1)
    chr2 = chr(ord('A') + m)
    # Zero index to 1-index
    return col_abs + chr1 + chr2 + row_abs + str(row + 1)


class report_xlsx_format:
    decimal_format = '#,##0.00'
    date_format = '%Y-%m-%d'
    styles = {
        'xls_title': [('bold', True), ('font_size', 10)],
        'bold': [('bold', True)],
        'underline': [('underline', True)],
        'italic': [('italic', True)],
        'fill_green': [('bg_color', '#CCFFCC')],
        'fill_yellow': [('bg_color', '#FFFFCC')],
        'money': [('num_format', decimal_format)],
        'date': [('num_format', date_format)],
        'borders_all': [('border', 1)],
        'center': [('align', 'center')],
        'right': [('align', 'right')],
    }

    def _get_style(self, wb, keys):
        if not isinstance(keys, (list, tuple)):
            keys = (keys, )
        style = dict(reduce(
            lambda x, y: x+y, [self.styles[k] for k in keys]))
        style.setdefault('font_size', 9)
        return wb.add_format(style)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class GeneralLedgerXlsx(ReportXlsx, report_xlsx_format):
    column_sizes = [
        10,  # date
        8,  # period
        15,  # move
        8,  # journal,
        8,  # account_code
        30,  # partner
        25,  # ref
        45,  # label
        30,  # counterpart
        12,  # debit
        12,  # credit
        12,  # bal
        12,  # filtered_bal
        12,  # cumul_bal
        12,  # curr_bal
        12,  # curr_code
    ]

    def generate_xlsx_report(self, wb, data, objects):
        _p = AttrDict(self.parser_instance.localcontext)

        wb.formats[0].set_font_size(9)
        ws = wb.add_worksheet(_p.report_name.upper()[:31])
        ws.set_default_row(13)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        # ws.header_str = self.xls_headers['standard']
        # ws.footer_str = self.xls_footers['standard']

        # cf. account_report_general_ledger.mako
        initial_balance_text = {'initial_balance': _('Computed'),
                                'opening_balance': _('Opening Entries'),
                                False: _('No')}

        # Title
        row_pos = 0
        style_title = self._get_style(wb, 'xls_title')
        report_name = ' - '.join([_p.report_name.upper(),
                                 _p.company.partner_id.name,
                                 _p.company.currency_id.name])
        ws.write(row_pos, 0, report_name, style_title)

        for i, size in enumerate(self.column_sizes):
            ws.set_column(i, i, size)
        row_pos += 2

        # Header Table
        style_header1 = self._get_style(wb, ('bold', 'fill_green', 'center'))
        style_header2 = self._get_style(wb, ('center'))

        ws.merge_range(
            row_pos, 0, row_pos, 1, _('Chart of Account'), style_header1)
        ws.merge_range(
            row_pos+1, 0, row_pos+1, 1, _p.chart_account.name, style_header2)

        ws.write(row_pos, 2, _('Fiscal Year'), style_header1)
        ws.write(row_pos+1, 2, _p.fiscalyear.name if _p.fiscalyear else '-',
                 style_header2)

        df = _('From') + ': %s ' + _('To') + ': %s'
        if _p.filter_form(data) == 'filter_date':
            dfh = _('Dates Filter')
            df = df % (_p.start_date or '', _p.stop_date or '')
        else:
            dfh = _('Periods Filter')
            df = df % (_p.start_period and _p.start_period.name or '',
                       _p.stop_period and _p.stop_period.name or '')
        ws.merge_range(row_pos, 3, row_pos, 5, dfh, style_header1)
        ws.merge_range(row_pos+1, 3, row_pos+1, 5, df, style_header2)

        ws.write(row_pos, 6, _('Accounts Filter'), style_header1)
        text = _p.accounts(data) and ', '.join([
            account.code for account in _p.accounts(data)]) or _('All')
        ws.write(row_pos+1, 6, text, style_header2)

        ws.write(row_pos, 7, _('Target Moves'), style_header1)
        ws.write(row_pos+1, 7, _p.display_target_move(data), style_header2)

        ws.write(row_pos, 8, _('Initial Balance'), style_header1)
        text = initial_balance_text[_p.initial_balance_mode]
        ws.write(row_pos+1, 8, text, style_header2)
        row_pos += 2

        ws.freeze_panes(row_pos, 0)
        row_pos += 1

        # cell styles for ledger lines
        style_account = self._get_style(wb, ('bold'))
        style_labels = self._get_style(wb, ('fill_yellow'))
        style_labels_r = self._get_style(wb, ('fill_yellow', 'right', 'bold'))
        style_initial_balance = self._get_style(wb, ('italic', 'money'))
        # style_date = self._get_style(wb, ('date'))
        style_lines = self._get_style(wb, ('money'))
        style_sums = self._get_style(wb, ('fill_yellow', 'money', 'bold'))

        for account in _p.objects:
            display_initial_balance = _p['init_balance'][account.id] and \
                (_p['init_balance'][account.id].get(
                    'debit', 0.0) != 0.0 or
                    _p['init_balance'][account.id].get('credit', 0.0) != 0.0)
            if (not display_initial_balance and
                    not _p['ledger_lines'][account.id]):
                # no lines and no initial balance, do no show account in report
                continue

            # Write account
            name = ' - '.join([account.code, account.name])
            ws.write(row_pos, 0, name, style_account)
            row_pos += 1

            # Write labels
            ws.write_row(row_pos, 0, [
                _('Date'), _('Period'), _('Entry'), _('Journal'), _('Account'),
                _('Partner'), _('Reference'), _('Label'), _('Counterpart')],
                style_labels)
            ws.write_row(row_pos, 9, [
                _('Debit'), _('Credit'), _('Filtered Bal.'), _('Cumul. Bal.')
                ], style_labels_r)
            row_pos += 1

            row_start = row_pos
            cumul_balance = cumul_balance_curr = 0

            # Write initial balance
            if display_initial_balance:
                ws.write(row_pos, 8, _('Initial Balance'),
                         style_initial_balance)
                init_balance = _p['init_balance'][account.id]
                cumul_balance += init_balance.get('init_balance') or 0.0
                cumul_balance_curr += \
                    init_balance.get('init_balance_currency') or 0.0
                row = [
                    init_balance.get('debit') or 0.0,
                    init_balance.get('credit') or 0.0,
                    '',
                    cumul_balance,
                    ]
                if _p.amount_currency(data):
                    row.append(cumul_balance_curr)
                ws.write_row(row_pos, 9, row, style_initial_balance)
                row_pos += 1

            # Write lines
            for line in _p['ledger_lines'][account.id]:
                label_elements = [line.get('lname') or '']
                if line.get('invoice_number'):
                    label_elements.append(
                        "(%s)" % (line['invoice_number'],))
                label = ' '.join(label_elements)
                cumul_balance += line.get('balance') or 0.0
                if line['ldate']:
                    ws.write_string(row_pos, 0, line['ldate'])
                    # FIXME: date format not recognized
                    # ws.write_datetime(
                    #    row_pos, 0,
                    #    datetime.strptime(line['ldate'], '%Y-%m-%d'),
                    #    style_date)
                row = [
                    line.get('period_code') or '',
                    line.get('move_name') or '',
                    line.get('jcode') or '',
                    account.code,
                    line.get('partner_name') or '',
                    line.get('lref'),
                    label,
                    line.get('counterparts') or '',
                    line.get('debit', 0.0),
                    line.get('credit', 0.0),
                    line.get('balance', 0.0),
                    cumul_balance,
                    ]
                if _p.amount_currency(data):
                    cumul_balance_curr += line.get('amount_currency') or 0.0
                    row += [
                        line.get('amount_currency') or 0.0,
                        line.get('currency_code') or '',
                    ]
                ws.write_row(row_pos, 1, row, style_lines)
                row_pos += 1

            # Write Sums
            row = [
                _('Cumulated Balance on Account'),
                '=SUM(%s:%s)' % (cell(row_start, 9), cell(row_pos-1, 9)),
                '=SUM(%s:%s)' % (cell(row_start, 10), cell(row_pos-1, 10)),
                '=SUM(%s:%s)' % (cell(row_start, 11), cell(row_pos-1, 11)),
                '=%s-%s' % (cell(row_pos, 9), cell(row_pos, 10)),
                ]
            if _p.amount_currency(data):
                row += [
                    cumul_balance_curr,
                    line.get('currency_code') or '',
                ]
            ws.write_row(row_pos, 8, row, style_sums)
            row_pos += 1


GeneralLedgerXlsx('report.account.account_report_general_ledger_xlsx',
                  'account.account',
                  parser=GeneralLedgerWebkit)
