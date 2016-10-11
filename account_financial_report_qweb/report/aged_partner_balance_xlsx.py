# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class AgedPartnerBalanceXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(AgedPartnerBalanceXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Aged Partner Balance')

    def _get_report_columns(self, report):
        if not report.show_move_line_details:
            return {
                0: {'header': _('Partner'), 'field': 'partner', 'width': 70},
                1: {'header': _('Residual'),
                    'field': 'amount_residual',
                    'field_footer_total': 'cumul_amount_residual',
                    'type': 'amount',
                    'width': 14},
                2: {'header': _('Current'),
                    'field': 'current',
                    'field_footer_total': 'cumul_current',
                    'field_footer_percent': 'percent_current',
                    'type': 'amount',
                    'width': 14},
                3: {'header': _(u'Age ≤ 30 d.'),
                    'field': 'age_30_days',
                    'field_footer_total': 'cumul_age_30_days',
                    'field_footer_percent': 'percent_age_30_days',
                    'type': 'amount',
                    'width': 14},
                4: {'header': _(u'Age ≤ 60 d.'),
                    'field': 'age_60_days',
                    'field_footer_total': 'cumul_age_60_days',
                    'field_footer_percent': 'percent_age_60_days',
                    'type': 'amount',
                    'width': 14},
                5: {'header': _(u'Age ≤ 90 d.'),
                    'field': 'age_90_days',
                    'field_footer_total': 'cumul_age_90_days',
                    'field_footer_percent': 'percent_age_90_days',
                    'type': 'amount',
                    'width': 14},
                6: {'header': _(u'Age ≤ 120 d.'),
                    'field': 'age_120_days',
                    'field_footer_total': 'cumul_age_120_days',
                    'field_footer_percent': 'percent_age_120_days',
                    'type': 'amount',
                    'width': 14},
                7: {'header': _('Older'),
                    'field': 'older',
                    'field_footer_total': 'cumul_older',
                    'field_footer_percent': 'percent_older',
                    'type': 'amount',
                    'width': 14},
            }
        else:
            return {
                0: {'header': _('Date'), 'field': 'date', 'width': 11},
                1: {'header': _('Entry'), 'field': 'entry', 'width': 18},
                2: {'header': _('Journal'), 'field': 'journal', 'width': 8},
                3: {'header': _('Account'), 'field': 'account', 'width': 9},
                4: {'header': _('Partner'), 'field': 'partner', 'width': 25},
                5: {'header': _('Ref - Label'), 'field': 'label', 'width': 40},
                6: {'header': _('Due date'), 'field': 'date_due', 'width': 11},
                7: {'header': _('Residual'),
                    'field': 'amount_residual',
                    'field_footer_total': 'cumul_amount_residual',
                    'field_final_balance': 'amount_residual',
                    'type': 'amount',
                    'width': 14},
                8: {'header': _('Current'),
                    'field': 'current',
                    'field_footer_total': 'cumul_current',
                    'field_footer_percent': 'percent_current',
                    'field_final_balance': 'current',
                    'type': 'amount',
                    'width': 14},
                9: {'header': _(u'Age ≤ 30 d.'),
                    'field': 'age_30_days',
                    'field_footer_total': 'cumul_age_30_days',
                    'field_footer_percent': 'percent_age_30_days',
                    'field_final_balance': 'age_30_days',
                    'type': 'amount',
                    'width': 14},
                10: {'header': _(u'Age ≤ 60 d.'),
                     'field': 'age_60_days',
                     'field_footer_total': 'cumul_age_60_days',
                     'field_footer_percent': 'percent_age_60_days',
                     'field_final_balance': 'age_60_days',
                     'type': 'amount',
                     'width': 14},
                11: {'header': _(u'Age ≤ 90 d.'),
                     'field': 'age_90_days',
                     'field_footer_total': 'cumul_age_90_days',
                     'field_footer_percent': 'percent_age_90_days',
                     'field_final_balance': 'age_90_days',
                     'type': 'amount',
                     'width': 14},
                12: {'header': _(u'Age ≤ 120 d.'),
                     'field': 'age_120_days',
                     'field_footer_total': 'cumul_age_120_days',
                     'field_footer_percent': 'percent_age_120_days',
                     'field_final_balance': 'age_120_days',
                     'type': 'amount',
                     'width': 14},
                13: {'header': _('Older'),
                     'field': 'older',
                     'field_footer_total': 'cumul_older',
                     'field_footer_percent': 'percent_older',
                     'field_final_balance': 'older',
                     'type': 'amount',
                     'width': 14},
            }

    def _get_report_filters(self, report):
        return [
            [_('Date at filter'), report.date_at],
            [_('Target moves filter'),
                _('All posted entries') if report.only_posted_moves
                else _('All entries')],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _get_col_pos_footer_label(self, report):
        return 0 if not report.show_move_line_details else 5

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def _generate_report_content(self, workbook, report):
        if not report.show_move_line_details:
            # For each account
            for account in report.account_ids:
                # Write account title
                self.write_array_title(account.code + ' - ' + account.name)

                # Display array header for partners lines
                self.write_array_header()

                # Display partner lines
                for partner in account.partner_ids:
                    self.write_line(partner.line_ids)

                # Display account lines
                self.write_account_footer(report,
                                          account,
                                          _('Total'),
                                          'field_footer_total',
                                          self.format_header_right,
                                          self.format_header_amount,
                                          False)
                self.write_account_footer(report,
                                          account,
                                          _('Percents'),
                                          'field_footer_percent',
                                          self.format_right_bold_italic,
                                          self.format_percent_bold_italic,
                                          True)

                # 2 lines break
                self.row_pos += 2
        else:
            # For each account
            for account in report.account_ids:
                # Write account title
                self.write_array_title(account.code + ' - ' + account.name)

                # For each partner
                for partner in account.partner_ids:
                    # Write partner title
                    self.write_array_title(partner.name)

                    # Display array header for move lines
                    self.write_array_header()

                    # Display account move lines
                    for line in partner.move_line_ids:
                        self.write_line(line)

                    # Display ending balance line for partner
                    self.write_ending_balance(partner.line_ids)

                    # Line break
                    self.row_pos += 1

                # Display account lines
                self.write_account_footer(report,
                                          account,
                                          _('Total'),
                                          'field_footer_total',
                                          self.format_header_right,
                                          self.format_header_amount,
                                          False)
                self.write_account_footer(report,
                                          account,
                                          _('Percents'),
                                          'field_footer_percent',
                                          self.format_right_bold_italic,
                                          self.format_percent_bold_italic,
                                          True)

                # 2 lines break
                self.row_pos += 2

    def write_ending_balance(self, my_object):
        """
            Specific function to write ending partner balance
            for Aged Partner Balance
        """
        name = None
        label = _('Partner cumul aged balance')
        super(AgedPartnerBalanceXslx, self).write_ending_balance(
            my_object, name, label
        )

    def write_account_footer(self, report, account, label, field_name,
                             string_format, amount_format, amount_is_percent):
        """
            Specific function to write account footer for Aged Partner Balance
        """
        col_pos_footer_label = self._get_col_pos_footer_label(report)
        for col_pos, column in self.columns.iteritems():
            if col_pos == col_pos_footer_label or column.get(field_name):
                if col_pos == col_pos_footer_label:
                    value = label
                else:
                    value = getattr(account, column[field_name])
                cell_type = column.get('type', 'string')
                if cell_type == 'string' or col_pos == col_pos_footer_label:
                    self.sheet.write_string(self.row_pos, col_pos, value or '',
                                            string_format)
                elif cell_type == 'amount':
                    number = float(value)
                    if amount_is_percent:
                        number /= 100
                    self.sheet.write_number(self.row_pos, col_pos,
                                            number,
                                            amount_format)
            else:
                self.sheet.write_string(self.row_pos, col_pos, '',
                                        string_format)

        self.row_pos += 1


AgedPartnerBalanceXslx(
    'report.account_financial_report_qweb.report_aged_partner_balance_xlsx',
    'report_aged_partner_balance_qweb',
    parser=report_sxw.rml_parse
)
