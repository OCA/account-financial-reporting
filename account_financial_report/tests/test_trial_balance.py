
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from . import abstract_test


class TestTrialBalance(abstract_test.AbstractTest):
    """
        Technical tests for Trial Balance Report.
    """

    def _getReportModel(self):
        return self.env['report_trial_balance']

    def _getQwebReportName(self):
        return 'account_financial_report.report_trial_balance_qweb'

    def _getXlsxReportName(self):
        return 'a_f_r.report_trial_balance_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report.action_report_trial_balance_xlsx'

    def _getReportTitle(self):
        return 'Odoo Report'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.env.ref('base.main_company').id,
            'fy_start_date': time.strftime('%Y-01-01'),
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_balance_at_0': True},
            {'show_partner_details': True},
            {'only_posted_moves': True, 'hide_account_balance_at_0': True},
            {'only_posted_moves': True, 'show_partner_details': True},
            {'hide_account_balance_at_0': True, 'show_partner_details': True},
            {
                'only_posted_moves': True,
                'hide_account_balance_at_0': True,
                'show_partner_details': True
            },
        ]

    def _partner_test_is_possible(self, filters):
        return 'show_partner_details' in filters
