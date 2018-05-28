# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class TrialBalanceXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(TrialBalanceXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Trial Balance')

    def _get_report_columns(self, report):
        if not report.show_partner_details:
            res = {
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
            if report.foreign_currency:
                foreign_currency = {
                    6: {'header': _('Cur.'),
                        'field': 'currency_id',
                        'field_currency_balance': 'currency_id',
                        'type': 'many2one', 'width': 7},
                    7: {'header': _('Initial balance'),
                        'field': 'initial_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 14},
                    8: {'header': _('Ending balance'),
                        'field': 'final_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 14},
                }
                res = dict(res.items() + foreign_currency.items())
            return res
        else:
            res = {
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
            if report.foreign_currency:
                foreign_currency = {
                    5: {'header': _('Cur.'),
                        'field': 'currency_id',
                        'field_currency_balance': 'currency_id',
                        'type': 'many2one', 'width': 7},
                    6: {'header': _('Initial balance'),
                        'field': 'initial_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 14},
                    7: {'header': _('Ending balance'),
                        'field': 'final_balance_foreign_currency',
                        'type': 'amount_currency',
                        'width': 14},
                }
                res = dict(res.items() + foreign_currency.items())
            return res

    def _get_report_filters(self, report):
        return [
            [_('Date range filter'),
                _('From: %s To: %s') % (report.date_from, report.date_to)],
            [_('Target moves filter'),
                _('All posted entries') if report.only_posted_moves
                else _('All entries')],
            [_('Account balance at 0 filter'),
                _('Hide') if report.hide_account_balance_at_0 else _('Show')],
            [_('Show foreign currency'),
             _('Yes') if report.foreign_currency else _('No')],
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
                self.write_line(account, 'account')

            else:
                # Write account title
                self.write_array_title(account.code + ' - ' + account.name)

                # Display array header for partner lines
                self.write_array_header()

                # For each partner
                for partner in account.partner_ids:
                    # Display partner lines
                    self.write_line(partner, 'partner')

                # Display account footer line
                self.write_account_footer(account,
                                          account.code + ' - ' + account.name)

                # Line break
                self.row_pos += 2

    def write_line(self, line_object, type_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        if type_object == 'partner':
            line_object.currency_id = line_object.report_account_id.currency_id
        elif type_object == 'account':
            line_object.currency_id = line_object.currency_id
        super(TrialBalanceXslx, self).write_line(line_object)

    def write_account_footer(self, account, name_value):
        """Specific function to write account footer for Trial Balance"""
        format_amt = self._get_currency_amt_header_format(account)
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
            elif cell_type == 'many2one':
                self.sheet.write_string(
                    self.row_pos, col_pos, value.name or '',
                    self.format_header_right)
            elif cell_type == 'amount_currency' and account.currency_id:
                self.sheet.write_number(
                    self.row_pos, col_pos, float(value),
                    format_amt)
            else:
                self.sheet.write_string(
                    self.row_pos, col_pos, '',
                    self.format_header_right)
        self.row_pos += 1


TrialBalanceXslx(
    'report.account_financial_report_qweb.report_trial_balance_xlsx',
    'report_trial_balance_qweb',
    parser=report_sxw.rml_parse
)
