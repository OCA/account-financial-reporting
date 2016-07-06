# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw


class GeneralLedgerXslx(ReportXlsx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(GeneralLedgerXslx, self).__init__(
            name, table, rml, parser, header, store)

        # Initialisé à None car on ne peut pas les setter pour le moment
        self.row_pos = None
        self.format_right = None
        self.format_blod = None
        self.format_header_left = None
        self.format_header_center = None
        self.format_header_right = None
        self.format_header_amount = None
        self.format_amount = None
        self.sheet = None

        self.columns = {
            0: {'header': 'Date', 'field': 'date', 'width': 11},
            1: {'header': 'Entry', 'field': 'entry', 'width': 18},
            2: {'header': 'Journal', 'field': 'journal', 'width': 8},
            3: {'header': 'Account', 'field': 'account', 'width': 9},
            4: {'header': 'Partner', 'field': 'partner', 'width': 25},
            5: {'header': 'Ref - Label', 'field': 'label', 'width': 40},
            6: {'header': 'Cost center', 'field': 'cost_center', 'width': 15},
            7: {'header': 'Rec.', 'field': 'matching_number', 'width': 5},
            8: {'header': 'Debit',
                'field': 'debit',
                'field_initial_balance': 'initial_debit',
                'field_final_balance': 'final_debit',
                'type': 'amount',
                'width': 14},
            9: {'header': 'Credit',
                'field': 'credit',
                'field_initial_balance': 'initial_credit',
                'field_final_balance': 'final_credit',
                'type': 'amount',
                'width': 14},
            10: {'header': 'Cumul. Bal.',
                 'field': 'cumul_balance',
                 'field_initial_balance': 'initial_balance',
                 'field_final_balance': 'final_balance',
                 'type': 'amount',
                 'width': 14},
            11: {'header': 'Cur.', 'field': 'currency_name', 'width': 7},
            12: {'header': 'Amount cur.',
                 'field': 'amount_currency',
                 'type': 'amount',
                 'width': 14},
        }

        self.col_pos_initial_balance_label = 5
        self.col_count_final_balance_name = 5

        self.col_pos_final_balance_label = 5

        self.col_count_filter_name = 2
        self.col_count_filter_value = 2

        self.column_count = len(self.columns)

    def generate_xlsx_report(self, workbook, data, objects):
        report = objects

        report_name = 'General Ledger'

        filters = [
            ['Date range filter',
                'From: '+report.date_from+' To: '+report.date_to],
            ['Target moves filter',
                'All posted entries' if report.only_posted_moves
                else 'All entries'],
            ['Account balance at 0 filter',
                'Hide' if report.hide_account_balance_at_0 else 'Show'],
            ['Centralize filter',
                'Yes' if report.centralize else 'No'],
        ]

        self.row_pos = 0

        self.format_blod = workbook.add_format({'bold': True})
        self.format_right = workbook.add_format({'align': 'right'})
        self.format_header_left = workbook.add_format(
            {'bold': True,
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_center = workbook.add_format(
            {'bold': True,
             'align': 'center',
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_right = workbook.add_format(
            {'bold': True,
             'align': 'right',
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_amount = workbook.add_format(
            {'bold': True,
             'border': True,
             'bg_color': '#FFFFCC'})
        self.format_header_amount.set_num_format('#,##0.00')
        self.format_amount = workbook.add_format()
        self.format_amount.set_num_format('#,##0.00')
        std_cell_format = workbook.add_format({'bold': False,
                                               'align': 'left',
                                               'border': False,
                                               'bg_color': '#FFFFFF'})

        self.sheet = workbook.add_worksheet(report_name[:31])

        self.set_column_width()

        self.write_report_title(report_name)

        self.write_filters(filters)

        for account in report.account_ids:
            self.write_array_title(account.code + ' - ' + account.name)

            if account.move_line_ids:
                self.write_header()
                self.write_initial_balance(account)
                for line in account.move_line_ids:
                    self.write_line(line)

            elif account.is_partner_account:
                for partner in account.partner_ids:
                    self.write_array_title(partner.name)

                    self.write_header()
                    self.write_initial_balance(partner)
                    for line in partner.move_line_ids:
                        self.write_line(line)

                    self.write_ending_balance(partner, 'partner')
                    self.row_pos += 1

            self.write_ending_balance(account, 'account')
            self.row_pos += 2

    def set_column_width(self):
        for position, column in self.columns.iteritems():
            self.sheet.set_column(position, position, column['width'])

    def write_report_title(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, self.column_count - 1,
            title, self.format_blod
        )
        self.row_pos += 3

    def write_filters(self, filters):
        col_name = 1
        col_value = col_name + self.col_count_filter_name + 1
        for title, value in filters:
            self.sheet.merge_range(
                self.row_pos, col_name,
                self.row_pos, col_name + self.col_count_filter_name - 1,
                title, self.format_header_left)
            self.sheet.merge_range(
                self.row_pos, col_value,
                self.row_pos, col_value + self.col_count_filter_value - 1,
                value)
            self.row_pos += 1
        self.row_pos += 2

    def write_array_title(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, self.column_count - 1,
            title, self.format_blod
        )
        self.row_pos += 1

    def write_line(self, line_object):
        for col_pos, column in self.columns.iteritems():
            value = getattr(line_object, column['field'])
            cell_type = column.get('type', 'string')
            if cell_type == 'string':
                self.sheet.write_string(self.row_pos, col_pos, value or '')
            elif cell_type == 'amount':
                self.sheet.write_number(
                    self.row_pos, col_pos, float(value), self.format_amount
                )
        self.row_pos += 1

    def write_header(self):
        for col_pos, column in self.columns.iteritems():
            self.sheet.write(self.row_pos, col_pos, column['header'],
                             self.format_header_center)
        self.row_pos += 1

    def write_initial_balance(self, my_object):
        col_pos_label = self.col_pos_initial_balance_label
        self.sheet.write(self.row_pos, col_pos_label, 'Initial balance',
                         self.format_right)
        for col_pos, column in self.columns.iteritems():
            if column.get('field_initial_balance'):
                value = getattr(my_object, column['field_initial_balance'])
                cell_type = column.get('type', 'string')
                if cell_type == 'string':
                    self.sheet.write_string(self.row_pos, col_pos, value or '')
                elif cell_type == 'amount':
                    self.sheet.write_number(
                        self.row_pos, col_pos, float(value), self.format_amount
                    )
        self.row_pos += 1

    def write_ending_balance(self, my_object, type_object):
        if type_object == 'partner':
            name = my_object.name
            label = 'Partner ending balance'
        elif type_object == 'account':
            name = my_object.code + ' - ' + my_object.name
            label = 'Ending balance'
        for i in range(0, self.column_count):
            self.sheet.write(self.row_pos, i, '', self.format_header_right)
        row_count_name = self.col_count_final_balance_name
        row_pos = self.row_pos
        col_pos_label = self.col_pos_final_balance_label
        self.sheet.merge_range(
            row_pos, 0, row_pos, row_count_name - 1, name,
            self.format_header_left
        )
        self.sheet.write(row_pos, col_pos_label, label,
                         self.format_header_right)
        for col_pos, column in self.columns.iteritems():
            if column.get('field_final_balance'):
                value = getattr(my_object, column['field_final_balance'])
                cell_type = column.get('type', 'string')
                if cell_type == 'string':
                    self.sheet.write_string(self.row_pos, col_pos, value or '',
                                            self.format_header_right)
                elif cell_type == 'amount':
                    self.sheet.write_number(
                        self.row_pos, col_pos, float(value),
                        self.format_header_amount
                    )
        self.row_pos += 1


GeneralLedgerXslx('report.ledger.report.wizard.xlsx',
                  'report_general_ledger_qweb', parser=report_sxw.rml_parse)
