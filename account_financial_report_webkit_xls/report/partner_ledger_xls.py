# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import xlwt
from datetime import datetime
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.partners_ledger \
    import PartnersLedgerWebkit
from openerp.tools.translate import _
# import logging
# _logger = logging.getLogger(__name__)

_column_sizes = [
    ('date', 12),
    ('period', 12),
    ('move', 20),
    ('journal', 12),
    ('partner', 30),
    ('label', 58),
    ('rec', 12),
    ('debit', 15),
    ('credit', 15),
    ('cumul_bal', 15),
    ('curr_bal', 15),
    ('curr_code', 7),
]


class PartnerLedgerXls(report_xls):
    column_sizes = [x[1] for x in _column_sizes]

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

        # cf. account_report_partner_ledger.mako
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
        nbr_columns = 10
        if _p.amount_currency(data):
            nbr_columns = 12
        cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('coa', 2, 0, 'text', _('Chart of Account')),
            ('fy', 1, 0, 'text', _('Fiscal Year')),
            ('df', 2, 0, 'text', _p.filter_form(data) ==
             'filter_date' and _('Dates Filter') or _('Periods Filter')),
            ('af', 1, 0, 'text', _('Accounts Filter')),
            ('tm', 2, 0, 'text', _('Target Moves')),
            ('ib', nbr_columns - 8, 0, 'text', _('Initial Balance')),

        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style_center)

        cell_format = _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('coa', 2, 0, 'text', _p.chart_account.name),
            ('fy', 1, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-'),
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
            ('df', 2, 0, 'text', df),
            ('af', 1, 0, 'text', _('Custom Filter')
             if _p.partner_ids else _p.display_partner_account(data)),
            ('tm', 2, 0, 'text', _p.display_target_move(data)),
            ('ib', nbr_columns - 8, 0, 'text',
             initial_balance_text[_p.initial_balance_mode]),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style_center)
        ws.set_horz_split_pos(row_pos)
        row_pos += 1

        # Account Title Row
        cell_format = _xs['xls_title'] + _xs['bold'] + \
            _xs['fill'] + _xs['borders_all']
        account_cell_style = xlwt.easyxf(cell_format)
        account_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        account_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # Column Title Row
        cell_format = _xs['bold']
        c_title_cell_style = xlwt.easyxf(cell_format)

        # Column Header Row
        cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        c_hdr_cell_style = xlwt.easyxf(cell_format)
        c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])

        # Column Initial Balance Row
        cell_format = _xs['italic'] + _xs['borders_all']
        c_init_cell_style = xlwt.easyxf(cell_format)
        c_init_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # Column Cumulated balance Row
        cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        c_cumul_cell_style = xlwt.easyxf(cell_format)
        c_cumul_cell_style_right = xlwt.easyxf(cell_format + _xs['right'])
        c_cumul_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_cumul_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # Column Partner Row
        cell_format = _xs['bold']
        c_part_cell_style = xlwt.easyxf(cell_format)

        c_specs = [
            ('date', 1, 0, 'text', _('Date'), None, c_hdr_cell_style),
            ('period', 1, 0, 'text', _('Period'), None, c_hdr_cell_style),
            ('move', 1, 0, 'text', _('Entry'), None, c_hdr_cell_style),
            ('journal', 1, 0, 'text', _('Journal'), None, c_hdr_cell_style),
            ('partner', 1, 0, 'text', _('Partner'), None, c_hdr_cell_style),
            ('label', 1, 0, 'text', _('Label'), None, c_hdr_cell_style),
            ('rec', 1, 0, 'text', _('Rec.'), None, c_hdr_cell_style),
            ('debit', 1, 0, 'text', _('Debit'), None, c_hdr_cell_style_right),
            ('credit', 1, 0, 'text', _('Credit'),
             None, c_hdr_cell_style_right),
            ('cumul_bal', 1, 0, 'text', _('Cumul. Bal.'),
             None, c_hdr_cell_style_right),
        ]
        if _p.amount_currency(data):
            c_specs += [
                ('curr_bal', 1, 0, 'text', _('Curr. Bal.'),
                 None, c_hdr_cell_style_right),
                ('curr_code', 1, 0, 'text', _('Curr.'),
                 None, c_hdr_cell_style_center),
            ]
        c_hdr_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])

        # cell styles for ledger lines
        ll_cell_format = _xs['borders_all']
        ll_cell_style = xlwt.easyxf(ll_cell_format)
        ll_cell_style_center = xlwt.easyxf(ll_cell_format + _xs['center'])
        ll_cell_style_date = xlwt.easyxf(
            ll_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        ll_cell_style_decimal = xlwt.easyxf(
            ll_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        cnt = 0
        for account in objects:
            if _p['ledger_lines'].get(account.id, False) or \
                    _p['init_balance'].get(account.id, False):
                if not _p['partners_order'].get(account.id, False):
                    continue
                cnt += 1
                account_total_debit = 0.0
                account_total_credit = 0.0
                account_balance_cumul = 0.0
                account_balance_cumul_curr = 0.0
                c_specs = [
                    ('acc_title', nbr_columns, 0, 'text',
                     ' - '.join([account.code, account.name]), None,
                     account_cell_style),
                ]
                row_data = self.xls_row_template(
                    c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    ws, row_pos, row_data, c_title_cell_style)
                row_pos += 1

                for partner_name, p_id, p_ref, p_name in \
                        _p['partners_order'][account.id]:

                    total_debit = 0.0
                    total_credit = 0.0
                    cumul_balance = 0.0
                    cumul_balance_curr = 0.0
                    part_cumul_balance = 0.0
                    part_cumul_balance_curr = 0.0
                    c_specs = [
                        ('partner_title', nbr_columns, 0, 'text',
                         partner_name or _('No Partner'), None,
                         c_part_cell_style),
                    ]
                    row_data = self.xls_row_template(
                        c_specs, [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(
                        ws, row_pos, row_data, c_title_cell_style)
                    row_pos = self.xls_write_row(ws, row_pos, c_hdr_data)
                    row_start_partner = row_pos

                    total_debit = _p['init_balance'][account.id].get(
                        p_id, {}).get('debit') or 0.0
                    total_credit = _p['init_balance'][account.id].get(
                        p_id, {}).get('credit') or 0.0

                    init_line = False
                    if _p.initial_balance_mode and \
                            (total_debit or total_credit):
                        init_line = True

                        part_cumul_balance = \
                            _p['init_balance'][account.id].get(
                                p_id, {}).get('init_balance') or 0.0
                        part_cumul_balance_curr = \
                            _p['init_balance'][account.id].get(
                                p_id, {}).get('init_balance_currency') or 0.0
                        balance_forward_currency = \
                            _p['init_balance'][account.id].get(
                                p_id, {}).get('currency_name') or ''

                        cumul_balance += part_cumul_balance
                        cumul_balance_curr += part_cumul_balance_curr

                        debit_cell = rowcol_to_cell(row_pos, 7)
                        credit_cell = rowcol_to_cell(row_pos, 8)
                        init_bal_formula = debit_cell + '-' + credit_cell

                        # Print row 'Initial Balance' by partn
                        c_specs = [('empty%s' % x, 1, 0, 'text', None)
                                   for x in range(5)]
                        c_specs += [
                            ('init_bal', 1, 0, 'text', _('Initial Balance')),
                            ('rec', 1, 0, 'text', None),
                            ('debit', 1, 0, 'number', total_debit,
                             None, c_init_cell_style_decimal),
                            ('credit', 1, 0, 'number', total_credit,
                             None, c_init_cell_style_decimal),
                            ('cumul_bal', 1, 0, 'number', None,
                             init_bal_formula, c_init_cell_style_decimal),
                        ]
                        if _p.amount_currency(data):
                            c_specs += [
                                ('curr_bal', 1, 0, 'number',
                                 part_cumul_balance_curr,
                                 None, c_init_cell_style_decimal),
                                ('curr_code', 1, 0, 'text',
                                 balance_forward_currency),
                            ]
                        row_data = self.xls_row_template(
                            c_specs, [x[0] for x in c_specs])
                        row_pos = self.xls_write_row(
                            ws, row_pos, row_data, c_init_cell_style)

                    for line in _p['ledger_lines'][account.id].get(p_id, []):

                        total_debit += line.get('debit') or 0.0
                        total_credit += line.get('credit') or 0.0

                        label_elements = [line.get('lname') or '']
                        if line.get('invoice_number'):
                            label_elements.append(
                                "(%s)" % (line['invoice_number'],))
                        label = ' '.join(label_elements)
                        cumul_balance += line.get('balance') or 0.0

                        if init_line or row_pos > row_start_partner:
                            cumbal_formula = rowcol_to_cell(
                                row_pos - 1, 9) + '+'
                        else:
                            cumbal_formula = ''
                        debit_cell = rowcol_to_cell(row_pos, 7)
                        credit_cell = rowcol_to_cell(row_pos, 8)
                        cumbal_formula += debit_cell + '-' + credit_cell
                        # Print row ledger line data #

                        if line.get('ldate'):
                            c_specs = [
                                ('ldate', 1, 0, 'date', datetime.strptime(
                                    line['ldate'], '%Y-%m-%d'), None,
                                 ll_cell_style_date),
                            ]
                        else:
                            c_specs = [
                                ('ldate', 1, 0, 'text', None),
                            ]
                        c_specs += [
                            ('period', 1, 0, 'text',
                             line.get('period_code') or ''),
                            ('move', 1, 0, 'text',
                             line.get('move_name') or ''),
                            ('journal', 1, 0, 'text', line.get('jcode') or ''),
                            ('partner', 1, 0, 'text',
                             line.get('partner_name') or ''),
                            ('label', 1, 0, 'text', label),
                            ('rec_name', 1, 0, 'text',
                             line.get('rec_name') or ''),
                            ('debit', 1, 0, 'number', line.get('debit'),
                             None, ll_cell_style_decimal),
                            ('credit', 1, 0, 'number', line.get('credit'),
                             None, ll_cell_style_decimal),
                            ('cumul_bal', 1, 0, 'number', None,
                             cumbal_formula, ll_cell_style_decimal),
                        ]
                        if _p.amount_currency(data):
                            c_specs += [
                                ('curr_bal', 1, 0, 'number', line.get(
                                    'amount_currency') or 0.0, None,
                                 ll_cell_style_decimal),
                                ('curr_code', 1, 0, 'text', line.get(
                                    'currency_code') or '', None,
                                 ll_cell_style_center),
                            ]
                        row_data = self.xls_row_template(
                            c_specs, [x[0] for x in c_specs])
                        row_pos = self.xls_write_row(
                            ws, row_pos, row_data, ll_cell_style)
                    # end for line

                    # Print row Cumulated Balance by partner #
                    debit_partner_start = rowcol_to_cell(row_start_partner, 7)
                    debit_partner_end = rowcol_to_cell(row_pos - 1, 7)
                    debit_partner_total = 'SUM(' + debit_partner_start + \
                        ':' + debit_partner_end + ')'

                    credit_partner_start = rowcol_to_cell(row_start_partner, 8)
                    credit_partner_end = rowcol_to_cell(row_pos - 1, 8)
                    credit_partner_total = 'SUM(' + credit_partner_start + \
                        ':' + credit_partner_end + ')'

                    bal_partner_debit = rowcol_to_cell(row_pos, 7)
                    bal_partner_credit = rowcol_to_cell(row_pos, 8)
                    bal_partner_total = bal_partner_debit + \
                        '-' + bal_partner_credit

                    c_specs = [('empty%s' % x, 1, 0, 'text', None)
                               for x in range(5)]
                    c_specs += [
                        ('init_bal', 1, 0, 'text',
                         _('Cumulated balance on Partner')),
                        ('rec', 1, 0, 'text', None),
                        ('debit', 1, 0, 'number', None,
                         debit_partner_total, c_cumul_cell_style_decimal),
                        ('credit', 1, 0, 'number', None,
                         credit_partner_total, c_cumul_cell_style_decimal),
                        ('cumul_bal', 1, 0, 'number', None,
                         bal_partner_total, c_cumul_cell_style_decimal),
                    ]
                    if _p.amount_currency(data):
                        if account.currency_id:
                            c_specs += [('curr_bal', 1, 0, 'number',
                                         cumul_balance_curr or 0.0, None,
                                         c_cumul_cell_style_decimal)]
                        else:
                            c_specs += [('curr_bal', 1, 0, 'text',
                                         '-', None, c_cumul_cell_style_right)]
                        c_specs += [('curr_code', 1, 0, 'text',
                                     account.currency_id.name if
                                     account.currency_id else u'', None,
                                     c_cumul_cell_style_center)]
                    row_data = self.xls_row_template(
                        c_specs, [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(
                        ws, row_pos, row_data, c_cumul_cell_style)
                    row_pos += 1
                    account_total_debit += total_debit
                    account_total_credit += total_credit
                    account_balance_cumul += cumul_balance
                    account_balance_cumul_curr += cumul_balance_curr

                #  Print row Cumulated Balance by account #
                c_specs = [
                    ('acc_title', 5, 0, 'text', ' - '.
                     join([account.code, account.name])), ]
                c_specs += [
                    ('label', 1, 0, 'text', _('Cumulated balance on Account')),
                    ('rec', 1, 0, 'text', None),
                    ('debit', 1, 0, 'number', account_total_debit,
                     None, account_cell_style_decimal),
                    ('credit', 1, 0, 'number', account_total_credit,
                     None, account_cell_style_decimal),
                    ('cumul_bal', 1, 0, 'number', account_balance_cumul,
                     None, account_cell_style_decimal),
                ]
                if _p.amount_currency(data):
                    if account.currency_id:
                        c_specs += [('curr_bal', 1, 0, 'number',
                                     account_balance_cumul_curr or 0.0, None,
                                     account_cell_style_decimal)]
                    else:
                        c_specs += [('curr_bal', 1, 0, 'text',
                                     '-', None, account_cell_style_right)]
                    c_specs += [('curr_code', 1, 0, 'text',
                                 account.currency_id.name if
                                 account.currency_id else u'', None,
                                 account_cell_style)]
                row_data = self.xls_row_template(
                    c_specs, [x[0] for x in c_specs])
                row_pos = self.xls_write_row(
                    ws, row_pos, row_data, account_cell_style)
                row_pos += 2


PartnerLedgerXls('report.account.account_report_partner_ledger_xls',
                 'account.account',
                 parser=PartnersLedgerWebkit)
