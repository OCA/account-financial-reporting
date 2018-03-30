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
from datetime import datetime
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.print_journal \
    import PrintJournalWebkit
from openerp.tools.translate import _


class print_journal_xls(report_xls):
    column_sizes = [40, 20, 17, 17, 17, 17, 17, 17]
    
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
        initial_balance_text = {
            'initial_balance': _('Computed'),
            'opening_balance': _('Opening Entries'),
            False: _('No')
        }

        # Title
        cell_style = xlwt.easyxf(_xs['xls_title'])
        report_name = ' - '.join([
            _p.report_name.upper(),
            _p.company.partner_id.name,
            _p.company.currency_id.name
        ])
        c_specs = [('report_name', 1, 0, 'text', report_name),]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style
        )

        # write empty row to define column sizes
        c_sizes = self.column_sizes
        c_specs = [
            ('empty%s' % i, 1, c_sizes[i], 'text', None)
            for i in range(0, len(c_sizes))
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, set_column_size=True
        )
        # Header Table
        cell_format = _xs['bold'] + _xs['fill_blue'] + _xs['borders_all']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('fy', 1, 0, 'text', _('Chart of Account'), 
            None, cell_style_center), 
            ('af', 1, 0, 'text', _('Fiscal Year'), None, cell_style_center),
            ('df', 1, 0, 'text', _p.filter_form(data) ==
             'filter_date' and _('Dates Filter') or _('Periods Filter')),
            ('tm', 2, 0, 'text',  _('Journal Filter'), None, cell_style_center),
            ('coa', 1, 0, 'text', _('Target Moves'),
            None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style
        )

        cell_format = _xs['borders_all'] + _xs['wrap'] + _xs['top']
        cell_style = xlwt.easyxf(cell_format)
        cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_specs = [
            ('fy', 1, 0, 'text', _p.chart_account.name, 
            None, cell_style_center),
            ('af', 1, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-'),
        ]
        df = _('From') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.start_date if _p.start_date else u''
        else:
            df += _p.start_period.name if _p.start_period else u''
        df +=  _('\tTo') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.stop_date if _p.stop_date else u''
        else:
            df += _p.stop_period.name if _p.stop_period else u''
        c_specs += [
            ('df', 1, 0, 'text', df),
            ('tm', 2, 0, 'text', _p.journals(data) and ', '.join(
                [journal.name for journal in _p.journals(data)]) or _('All')),
            ('coa', 1, 0, 'text', _p.display_target_move(data),
             None, cell_style_center),
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(
            ws, row_pos, row_data, row_style=cell_style
        )

        # Column Title Row
        cell_format = _xs['bold']
        c_title_cell_style = xlwt.easyxf(cell_format)

        # Column Header Row
        cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        c_hdr_cell_style = xlwt.easyxf(cell_format)
        c_hdr_cell_style_right = xlwt.easyxf(cell_format + _xs['right'],
             num_format_str=report_xls.decimal_format)
        c_hdr_cell_style_center = xlwt.easyxf(cell_format + _xs['center'])
        c_hdr_cell_style_left = xlwt.easyxf(cell_format + _xs['left'])
        c_hdr_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # Column Initial Balance Row
        cell_format = _xs['italic'] + _xs['borders_all']
        c_init_cell_style = xlwt.easyxf(cell_format)
        c_init_cell_style_decimal = xlwt.easyxf(
            cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        c_specs = [
            ('date', 1, 0, 'text', _('Date'), None, c_hdr_cell_style),
            ('period', 1, 0, 'text', _('Entry'), None, c_hdr_cell_style),
            ('move', 1, 0, 'text', _('Account'), None, c_hdr_cell_style),
            ('Due Date', 1, 0, 'text', _('Due Date'),
             None, c_hdr_cell_style),
            ('partner', 1, 0, 'text', _('Partner'), None, c_hdr_cell_style),
            ('label', 1, 0, 'text', _('Label'), None, c_hdr_cell_style),
            ('debit', 1, 0, 'text', _('Debit'), None, c_hdr_cell_style_right),
            ('credit', 1, 0, 'text', _('Credit'),
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

        for journal_period in objects:
            # write empty row to define column sizes
            c_sizes = self.column_sizes
            c_specs = [
                ('empty%s' % i, 1, c_sizes[i], 'text', None)
                for i in range(0, len(c_sizes))
            ]
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, set_column_size=True
            )
            account_total_debit = 0.0
            account_total_credit = 0.0
            account_total_currency = 0.0
            acc_title = ' - '.join(
                [journal_period.journal_id.name, 
                journal_period.period_id.name]
            )
            c_specs = [
                ('acc_title', 5, 0, 'text', acc_title )
            ]
            row_data = self.xls_row_template(
                c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, c_title_cell_style)
            row_pos = self.xls_write_row(ws, row_pos, c_hdr_data)
            for move in journal_period.moves:
                for line in move.line_id:
                    account_total_debit += line.debit or 0.0
                    account_total_credit += line.credit or 0.0
                    date = datetime.strptime(move.date, '%Y-%m-%d')
                    account_move = move.name or ''
                    code = line.account_id.code
                    due_date = line.date_maturity or ''
                    partner = line.partner_id.name or  ''
                    label = line.name
                    debit = line.debit if line.debit else ''
                    credit = line.credit if line.credit else ''
                    if _p.amount_currency(data):
                            ## currency balance
                            amt_currency = (
                                line.amount_currency if line.amount_currency else ''
                            )
                            ## curency code
                            code_currency = line.currency_id.symbol or ''
                    c_specs = [
                        ('date', 1, 0, 'date', date, None, ll_cell_style_date),
                        ('period', 1, 0, 'text', account_move),
                        ('move', 1, 0, 'text', code),
                        ('Due Date', 1, 0, 'text', due_date),
                        ('partner', 1, 0, 'text', partner),
                        ('label', 1, 0, 'text', label),
                        ('debit', 1, 0, 'number', debit, 
                         None, ll_cell_style_decimal),
                        ('credit', 1, 0, 'number', credit,
                         None, ll_cell_style_decimal),
                    ]
                    if _p.amount_currency(data):
                        c_specs += [
                            ('curr_bal', 1, 0, 'text', amt_currency,
                             None, c_hdr_cell_style_right),
                            ('curr_code', 1, 0, 'text', code_currency,
                             None, c_hdr_cell_style_center),
                        ]
                    row_data = self.xls_row_template(
                        c_specs, [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(
                        ws, row_pos, row_data, ll_cell_style)
                    c_specs = [
                        ('acc_title', 6, 0, 'text', acc_title, 
                         None, c_hdr_cell_style_left)
                    ]
            c_specs += [
                    ('amount_debit', 1, 0, 'number', 
                    account_total_debit, None, 
                    c_hdr_cell_style_right),
                    ('amount_credir', 1, 0, 'number', 
                    account_total_credit, None, 
                    c_hdr_cell_style_right),
                ]
            row_data = self.xls_row_template(
                c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, c_init_cell_style)
            
        
print_journal_xls('report.account.account_report_journal_xls',
                   'account.account',
                   parser=PrintJournalWebkit)
                             

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: