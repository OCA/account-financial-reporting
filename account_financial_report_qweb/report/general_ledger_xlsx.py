# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from openerp.report import report_sxw


class GeneralLedgerXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(GeneralLedgerXslx, self).__init__(
            name, table, rml, parser, header, store)

        # Custom values needed to generate report
        self.col_pos_initial_balance_label = 5
        self.col_count_final_balance_name = 5
        self.col_pos_final_balance_label = 5

    def _get_report_name(self):
        return 'General Ledger'

    def _get_report_columns(self):
        return {
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

    def _get_report_filters(self, report):
        return [
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

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _generate_report_content(self, workbook, report):
        # For each account
        for account in report.account_ids:
            # Write account title
            self.write_array_title(account.code + ' - ' + account.name)

            if account.move_line_ids:
                # Display array header for move lines
                self.write_array_header()

                # Display initial balance line for account
                self.write_initial_balance(account)

                # Display account move lines
                for line in account.move_line_ids:
                    self.write_line(line)

            elif account.is_partner_account:
                # For each partner
                for partner in account.partner_ids:
                    # Write partner title
                    self.write_array_title(partner.name)

                    # Display array header for move lines
                    self.write_array_header()

                    # Display initial balance line for partner
                    self.write_initial_balance(partner)

                    # Display account move lines
                    for line in partner.move_line_ids:
                        self.write_line(line)

                    # Display ending balance line for partner
                    self.write_ending_balance(partner, 'partner')

                    # Line break
                    self.row_pos += 1

            # Display ending balance line for account
            self.write_ending_balance(account, 'account')

            # 2 lines break
            self.row_pos += 2

    def write_initial_balance(self, my_object):
        """Specific function to write initial balance for General Ledger"""
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
        """Specific function to write ending balance for General Ledger"""
        if type_object == 'partner':
            name = my_object.name
            label = 'Partner ending balance'
        elif type_object == 'account':
            name = my_object.code + ' - ' + my_object.name
            label = 'Ending balance'
        for i in range(0, len(self.columns)):
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
