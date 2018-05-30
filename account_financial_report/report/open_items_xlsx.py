# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class OpenItemsXslx(models.AbstractModel):
    _name = 'report.a_f_r.report_open_items_xlsx'
    _inherit = 'report.account_financial_report.abstract_report_xlsx'

    def _get_report_name(self):
        return _('Open Items')

    def _get_report_columns(self, report):
        res = {
            0: {'header': _('Date'), 'field': 'date', 'width': 11},
            1: {'header': _('Entry'), 'field': 'entry', 'width': 18},
            2: {'header': _('Journal'), 'field': 'journal', 'width': 8},
            3: {'header': _('Account'), 'field': 'account', 'width': 9},
            4: {'header': _('Partner'), 'field': 'partner', 'width': 25},
            5: {'header': _('Ref - Label'), 'field': 'label', 'width': 40},
            6: {'header': _('Due date'), 'field': 'date_due', 'width': 11},
            7: {'header': _('Original'),
                'field': 'amount_total_due',
                'type': 'amount',
                'width': 14},
            8: {'header': _('Residual'),
                'field': 'amount_residual',
                'field_final_balance': 'final_amount_residual',
                'type': 'amount',
                'width': 14},
        }
        if report.foreign_currency:
            foreign_currency = {
                9: {'header': _('Cur.'), 'field': 'currency_id',
                    'field_currency_balance': 'currency_id',
                    'type': 'many2one', 'width': 7},
                10: {'header': _('Cur. Original'),
                     'field': 'amount_total_due_currency',
                     'field_final_balance':
                         'final_amount_total_due_currency',
                     'type': 'amount_currency',
                     'width': 14},
                11: {'header': _('Cur. Residual'),
                     'field': 'amount_residual_currency',
                     'field_final_balance':
                         'final_amount_residual_currency',
                     'type': 'amount_currency',
                     'width': 14},
            }
            res = {**res, **foreign_currency}
        return res

    def _get_report_filters(self, report):
        return [
            [_('Date at filter'), report.date_at],
            [_('Target moves filter'),
             _('All posted entries') if report.only_posted_moves else _(
                 'All entries')],
            [_('Account balance at 0 filter'),
             _('Hide') if report.hide_account_balance_at_0 else _('Show')],
            [_('Show foreign currency'),
             _('Yes') if report.foreign_currency else _('No')],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_col_count_final_balance_name(self):
        return 5

    def _get_col_pos_final_balance_label(self):
        return 5

    def _generate_report_content(self, workbook, report):
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
                self.write_ending_balance(partner, 'partner')

                # Line break
                self.row_pos += 1

            # Display ending balance line for account
            self.write_ending_balance(account, 'account')

            # 2 lines break
            self.row_pos += 2

    def write_ending_balance(self, my_object, type_object):
        """Specific function to write ending balance for Open Items"""
        if type_object == 'partner':
            name = my_object.name
            label = _('Partner ending balance')
            my_object.currency_id = my_object.report_account_id.currency_id
        elif type_object == 'account':
            name = my_object.code + ' - ' + my_object.name
            label = _('Ending balance')
        super(OpenItemsXslx, self).write_ending_balance(my_object, name, label)
