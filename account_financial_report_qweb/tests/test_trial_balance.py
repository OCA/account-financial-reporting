# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from . import abstract_test_foreign_currency as a_t_f_c


class TestTrialBalance(a_t_f_c.AbstractTestForeignCurrency):
    """
        Technical tests for Trial Balance Report.
    """

    def _getReportModel(self):
        return self.env['report_trial_balance_qweb']

    def _getQwebReportName(self):
        return 'account_financial_report_qweb.report_trial_balance_qweb'

    def _getXlsxReportName(self):
        return 'account_financial_report_qweb.report_trial_balance_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report_qweb.action_report_trial_balance_xlsx'

    def _getReportTitle(self):
        return 'Trial Balance'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.env.ref('base.main_company').id,
            'fy_start_date': time.strftime('%Y-01-01'),
            'foreign_currency': True,
            'show_partner_details': True,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_at_0': True},
            {'show_partner_details': True},
            {'only_posted_moves': True, 'hide_account_at_0': True},
            {'only_posted_moves': True, 'show_partner_details': True},
            {'hide_account_at_0': True, 'show_partner_details': True},
            {
                'only_posted_moves': True,
                'hide_account_at_0': True,
                'show_partner_details': True
            },
        ]

    def _partner_test_is_possible(self, filters):
        return 'show_partner_details' in filters
