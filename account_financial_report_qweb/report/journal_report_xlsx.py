# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class JournalXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(
            self, name, table, rml=False, parser=False, header=True,
            store=False):
        super(JournalXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Journal')

    def _get_report_columns(self, report):
        columns = [
            {
                'header': _('Entry'),
                'field': 'entry',
                'width': 18
            },
            {
                'header': _('Date'),
                'field': 'date',
                'width': 11
            },
            {
                'header': _('Account'),
                'field': 'account_code',
                'width': 9
            },
        ]

        if report.with_account_name:
            columns.append({
                'header': _('Account Name'),
                'field': 'account',
                'width': 15
            })

        columns += [
            {
                'header': _('Partner'),
                'field': 'partner',
                'width': 25
            },
            {
                'header': _('Ref - Label'),
                'field': 'label',
                'width': 40
            },
            {
                'header': _('Taxes'),
                'field': 'taxes_description',
                'width': 11
            },
            {
                'header': _('Debit'),
                'field': 'debit',
                'type': 'amount',
                'width': 14,
            },
            {
                'header': _('Credit'),
                'field': 'credit',
                'type': 'amount',
                'width': 14
            }
        ]

        if report.foreign_currency:
            columns += [
                {
                    'header': _('Amount Currency'),
                    'field': 'amount_currency',
                    'type': 'amount',
                    'width': 14
                },
                {
                    'header': _('Currency'),
                    'field': 'currency_name',
                    'width': 14
                }
            ]

        columns_as_dict = {}
        for i, column in enumerate(columns):
            columns_as_dict[i] = column
        return columns_as_dict

    def _get_journal_tax_columns(self, report):
        return {
            0: {
                'header': _('Name'),
                'field': 'tax_name',
                'width': 35
            },
            1: {
                'header': _('Description'),
                'field': 'tax_code',
                'width': 18
            },
            2: {
                'header': _('Base Debit'),
                'field': 'base_debit',
                'type': 'amount',
                'width': 14
            },
            3: {
                'header': _('Base Credit'),
                'field': 'base_credit',
                'type': 'amount',
                'width': 14
            },
            4: {
                'header': _('Base Balance'),
                'field': 'base_balance',
                'type': 'amount',
                'width': 14
            },
            5: {
                'header': _('Tax Debit'),
                'field': 'tax_debit',
                'type': 'amount',
                'width': 14
            },
            6: {
                'header': _('Tax Credit'),
                'field': 'tax_credit',
                'type': 'amount',
                'width': 14
            },
            7: {
                'header': _('Tax Balance'),
                'field': 'tax_balance',
                'type': 'amount',
                'width': 14
            },
        }

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _get_report_filters(self, report):
        target_label_by_value = {
            value: label
            for value, label in
            self.env['journal.report.wizard']._get_move_targets()
        }

        sort_option_label_by_value = {
            value: label
            for value, label in
            self.env['journal.report.wizard']._get_sort_options()
        }

        return [
            [
                _('Company'),
                report.company_id.name
            ],
            [
                _('Date range filter'),
                _('From: %s To: %s') % (report.date_from, report.date_to)
            ],
            [
                _('Target moves filter'),
                _("%s") % target_label_by_value[report.move_target],
            ],
            [
                _('Entries sorted by'),
                _("%s") % sort_option_label_by_value[report.sort_option],
            ],
            [
                _('Journals'),
                ', '.join([
                    "%s - %s" % (report_journal.code, report_journal.name)
                    for report_journal in report.report_journal_ids
                ])

            ]
        ]

    def _generate_report_content(self, workbook, report):
        group_option = report.group_option
        if group_option == 'journal':
            for report_journal in report.report_journal_ids:
                self._generate_journal_content(workbook, report_journal)
        elif group_option == 'none':
            self._generate_no_group_content(workbook, report)

    def _generate_no_group_content(self, workbook, report):
        self._generate_moves_content(
            workbook, report, "Report", report.report_move_ids)
        self._generate_no_group_taxes_summary(workbook, report)

    def _generate_journal_content(self, workbook, report_journal):
        sheet_name = "%s (%s) - %s" % (
            report_journal.code,
            report_journal.currency_id.name,
            report_journal.name,
        )
        self._generate_moves_content(
            workbook, report_journal.report_id, sheet_name,
            report_journal.report_move_ids)
        self._generate_journal_taxes_summary(workbook, report_journal)

    def _generate_no_group_taxes_summary(self, workbook, report):
        self._generate_taxes_summary(
            workbook, report, "Tax Report", report.report_tax_line_ids)

    def _generate_journal_taxes_summary(self, workbook, report_journal):
        sheet_name = "Tax - %s (%s) - %s" % (
            report_journal.code,
            report_journal.currency_id.name,
            report_journal.name,
        )
        report = report_journal.report_id
        self._generate_taxes_summary(
            workbook, report, sheet_name, report_journal.report_tax_line_ids)

    def _generate_moves_content(self, workbook, report, sheet_name, moves):
        report_sheet = self.add_sheet(workbook, sheet_name)
        self.set_sheet(report_sheet)
        self._set_column_width()

        self.row_pos = 1

        self.write_array_title(sheet_name)
        self.row_pos += 2

        self.write_array_header()
        for move in moves:
            for line in move.report_move_line_ids:
                self.write_line(line)
            self.row_pos += 1

    def _generate_taxes_summary(self, workbook, report, sheet_name, tax_lines):
        tax_journal_sheet = self.add_sheet(workbook, sheet_name)
        self.set_sheet(tax_journal_sheet)

        self.row_pos = 1
        self.write_array_title(sheet_name)
        self.row_pos += 2

        tax_columns = self._get_journal_tax_columns(report)
        self._set_columns_width(tax_columns)

        for col_pos, column in tax_columns.iteritems():
            self.sheet.write(
                self.row_pos, col_pos, column['header'],
                self.format_header_center
            )
        self.row_pos += 1
        for tax_line in tax_lines:
            self._write_line(tax_columns, tax_line)


JournalXslx(
    'report.account_financial_report_qweb.report_journal_xlsx',
    'report_journal_qweb',
    parser=report_sxw.rml_parse
)
