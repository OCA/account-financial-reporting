# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class VATReportXslx(models.AbstractModel):
    _name = 'report.a_f_r.report_vat_report_xlsx'
    _inherit = 'report.account_financial_report.abstract_report_xlsx'

    def _get_report_name(self, report):
        report_name = _('VAT Report')
        return self._get_report_complete_name(report, report_name)

    def _get_report_columns(self, report):
        return {
            0: {'header': _('Code'), 'field': 'code', 'width': 5},
            1: {'header': _('Name'), 'field': 'name', 'width': 100},
            2: {'header': _('Net'),
                'field': 'net',
                'type': 'amount',
                'width': 14},
            3: {'header': _('Tax'),
                'field': 'tax',
                'type': 'amount',
                'width': 14},
        }

    def _get_report_filters(self, report):
        return [
            [_('Date from'), report.date_from],
            [_('Date to'), report.date_to],
            [_('Based on'), report.based_on],
        ]

    def _get_col_count_filter_name(self):
        return 0

    def _get_col_count_filter_value(self):
        return 2

    def _generate_report_content(self, workbook, report):
        # For each taxtag
        self.write_array_header()
        for taxtag in report.taxtags_ids:
            # Write taxtag line
            self.write_line(taxtag)

            # For each tax if detail taxes
            if report.tax_detail:
                for tax in taxtag.tax_ids:
                    self.write_line(tax)
