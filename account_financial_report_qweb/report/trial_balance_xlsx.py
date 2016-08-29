# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from openerp.report import report_sxw
from openerp import _


class TrialBalanceXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(TrialBalanceXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Trial Balance')

    def _get_report_columns(self, report):
        if not report.show_partner_details:
            return {
                0: {'header': _('Code'), 'field': 'code', 'width': 10},
                1: {'header': _('Account'), 'field': 'name', 'width': 60},
                2: {'header': _('Initial balance'),
                    'field': 'initial_balance',
                    'type': 'amount',
                    'width': 14},
                3: {'header': _('Debit'),
                    'field': 'debit',
                    'type': 'amount',
                    'width': 14},
                4: {'header': _('Credit'),
                    'field': 'credit',
                    'type': 'amount',
                    'width': 14},
                5: {'header': _('Ending balance'),
                    'field': 'final_balance',
                    'type': 'amount',
                    'width': 14},
            }
        else:
            return {
                0: {'header': _('Partner'), 'field': 'name', 'width': 70},
                1: {'header': _('Initial balance'),
                    'field': 'initial_balance',
                    'type': 'amount',
                    'width': 14},
                2: {'header': _('Debit'),
                    'field': 'debit',
                    'type': 'amount',
                    'width': 14},
                3: {'header': _('Credit'),
                    'field': 'credit',
                    'type': 'amount',
                    'width': 14},
                4: {'header': _('Ending balance'),
                    'field': 'final_balance',
                    'type': 'amount',
                    'width': 14},
            }

    def _get_report_filters(self, report):
        return [
            [_('Date range filter'),
                _('From: %s To: %s') % (report.date_from, report.date_to)],
            [_('Target moves filter'),
                _('All posted entries') if report.only_posted_moves
                else _('All entries')],
            [_('Account balance at 0 filter'),
                _('Hide') if report.hide_account_balance_at_0 else _('Show')],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _generate_report_content(self, workbook, report):

        if not report.show_partner_details:
            # Display array header for account lines
            self.write_array_header()

        # For each account
        for account in report.account_ids:
            if not report.show_partner_details:
                # Display account lines
                self.write_line(account)

            else:
                # Write account title
                self.write_array_title(account.code + ' - ' + account.name)

                # Display array header for partner lines
                self.write_array_header()

                # For each partner
                for partner in account.partner_ids:
                    # Display partner lines
                    self.write_line(partner)

                # Display account footer line
                self.write_account_footer(account,
                                          account.code + ' - ' + account.name)

                # Line break
                self.row_pos += 2

    def write_account_footer(self, account, name_value):
        """Specific function to write account footer for Trial Balance"""
        for col_pos, column in self.columns.iteritems():
            if column['field'] == 'name':
                value = name_value
            else:
                value = getattr(account, column['field'])
            cell_type = column.get('type', 'string')
            if cell_type == 'string':
                self.sheet.write_string(self.row_pos, col_pos, value or '',
                                        self.format_header_left)
            elif cell_type == 'amount':
                self.sheet.write_number(self.row_pos, col_pos, float(value),
                                        self.format_header_amount)
        self.row_pos += 1


TrialBalanceXslx(
    'report.account_financial_report_qweb.report_trial_balance_xlsx',
    'report_trial_balance_qweb',
    parser=report_sxw.rml_parse
)
