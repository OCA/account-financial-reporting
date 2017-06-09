# -*- coding: utf-8 -*-
# Copyright 2017 RGB Consulting S.L. (http://www.rgbconsulting.com)
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
#                Miquel Raich <miquel.raich@eficent.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object
from openerp.report import report_sxw
from openerp import _


class JournalLedgerXlsx(ReportXlsx):
    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(ReportXlsx, self).__init__(
            name, table, rml, parser, header, store)

        self.sheet = None
        self.row_pos = None

        self.format_title = None
        self.format_border_top = None

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
         * format_header_right
         * format_header_italic
         * format_border_top
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#46C646',
            'border': True
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True
        })
        self.format_header_right = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True,
            'align': 'right'
        })
        self.format_header_italic = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True,
            'italic': True
        })
        self.format_border_top = workbook.add_format({
            'top': 1,
            'bg_color': '#eeeeee'
        })

    def _write_report_title(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 6, title, self.format_title
        )
        self.row_pos += 1

    def _write_report_range(self, date1, date2):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 1,
            _('From ')+date1+_(' to ')+date2+_(':'))
        self.row_pos += 1

    def _set_headers(self):
        # Journal
        self.sheet.write_string(self.row_pos, 2, _('Journal'),
                                self.format_header)
        # Partner
        self.sheet.write_string(self.row_pos, 3, _('Partner'),
                                self.format_header)
        # Reference
        self.sheet.write_string(self.row_pos, 4, _('Reference'),
                                self.format_header)
        self.row_pos += 1
        # Entry
        self.sheet.write_string(self.row_pos, 0, _('Entry'),
                                self.format_header)
        # Date
        self.sheet.write_string(self.row_pos, 1, _('Date'), self.format_header)

        # Account
        self.sheet.write_string(self.row_pos, 2, _('Account'),
                                self.format_header_italic)
        # Account name
        self.sheet.write_string(self.row_pos, 3, _('Account name'),
                                self.format_header_italic)
        # Description
        self.sheet.write_string(self.row_pos, 4, _('Description'),
                                self.format_header_italic)
        # Debit
        self.sheet.write_string(self.row_pos, 5, _('Debit'),
                                self.format_header_right)
        # Credit
        self.sheet.write_string(self.row_pos, 6, _('Credit'),
                                self.format_header_right)
        self.sheet.freeze_panes(4, 0)
        self.row_pos += 1

    def _generate_report_content(self, report_data):
        for move in report_data:
            # Entry
            self.sheet.write_string(self.row_pos, 0, move.name or '',
                                    self.format_border_top)
            self.sheet.set_column(0, 0, 18)
            # Date
            self.sheet.write_string(self.row_pos, 1, move.date or '',
                                    self.format_border_top)
            self.sheet.set_column(1, 1, 12)
            # Journal
            self.sheet.write_string(self.row_pos, 2,
                                    move.journal_id.name or '',
                                    self.format_border_top)
            self.sheet.set_column(2, 2, 30)
            # Partner
            self.sheet.write_string(self.row_pos, 3,
                                    move.partner_id.name or '',
                                    self.format_border_top)
            self.sheet.set_column(3, 3, 40)
            # Reference
            self.sheet.write_string(self.row_pos, 4, move.ref or '',
                                    self.format_border_top)
            self.sheet.set_column(4, 4, 40)
            # Debit
            self.sheet.write_number(self.row_pos, 5, move.amount or 0,
                                    self.format_border_top)
            self.sheet.set_column(5, 5, 12)
            # Credit
            self.sheet.write_number(self.row_pos, 6, move.amount or 0,
                                    self.format_border_top)
            self.sheet.set_column(6, 6, 12)

            self.row_pos += 1
            for line in move.line_ids:
                # Account code
                self.sheet.write_string(self.row_pos, 2,
                                        line.account_id.code or '')
                # Account name
                self.sheet.write_string(self.row_pos, 3,
                                        line.account_id.name or '')
                # Line description
                self.sheet.write_string(self.row_pos, 4, line.name or '')
                # Debit
                self.sheet.write_number(self.row_pos, 5, line.debit or 0)
                # Credit
                self.sheet.write_number(self.row_pos, 6, line.credit or 0)
                self.row_pos += 1

    def generate_xlsx_report(self, workbook, data, objects):
        date_start = data.get('date_start')
        date_end = data.get('date_end')
        journal_ids = data.get('journal_ids', [])

        report_data = self.env['account.move'].search(
            [('date', '<=', date_end),
             ('date', '>=', date_start),
             ('journal_id', 'in', journal_ids),
             ('state', '!=', 'draft')],
            order=data.get('sort_selection', 'date') + ', id')

        # Initial row
        self.row_pos = 0

        # Load formats to workbook
        self._define_formats(workbook)

        # Set report name
        report_name = _('Journal Ledger') + ' - ' + \
            self.env.user.company_id.name
        self.sheet = workbook.add_worksheet(report_name[:31])
        if data.get('landscape'):
            self.sheet.set_landscape()
        self.sheet.fit_to_pages(1, 0)
        self.sheet.set_zoom(80)
        self._write_report_title(report_name)
        self._write_report_range(date_start, date_end)

        # Set headers
        self._set_headers()

        # Generate data
        self._generate_report_content(report_data)


if ReportXlsx != object:
    JournalLedgerXlsx(
        'report.account_journal_report.journal_ledger_xlsx',
        'account.journal', parser=report_sxw.rml_parse
    )
