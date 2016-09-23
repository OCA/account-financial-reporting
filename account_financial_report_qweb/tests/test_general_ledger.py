# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from . import abstract_test


class TestGeneralLedger(abstract_test.AbstractTest):
    """
        Technical tests for General Ledger Report.
    """

    def _getReportModel(self):
        return self.env['report_general_ledger_qweb']

    def _getQwebReportName(self):
        return 'account_financial_report_qweb.report_general_ledger_qweb'

    def _getXlsxReportName(self):
        return 'account_financial_report_qweb.report_general_ledger_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report_qweb.' \
               'action_report_general_ledger_xlsx'

    def _getReportTitle(self):
        return 'General Ledger'

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
            {'centralize': True},
            {'only_posted_moves': True, 'hide_account_balance_at_0': True},
            {'only_posted_moves': True, 'centralize': True},
            {'hide_account_balance_at_0': True, 'centralize': True},
            {
                'only_posted_moves': True,
                'hide_account_balance_at_0': True,
                'centralize': True
            },
            {'enable_counterpart_accounts': True},
        ]
