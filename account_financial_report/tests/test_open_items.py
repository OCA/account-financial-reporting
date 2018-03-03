# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from . import abstract_test


class TestOpenItems(abstract_test.AbstractTest):
    """
        Technical tests for Open Items Report.
    """

    def _getReportModel(self):
        return self.env['report_open_items']

    def _getQwebReportName(self):
        return 'account_financial_report.report_open_items_qweb'

    def _getXlsxReportName(self):
        return 'a_f_r.report_open_items_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report.action_report_open_items_xlsx'

    def _getReportTitle(self):
        return 'Odoo'

    def _getBaseFilters(self):
        return {
            'date_at': time.strftime('%Y-12-31'),
            'company_id': self.company.id,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_balance_at_0': True},
            {'only_posted_moves': True, 'hide_account_balance_at_0': True},
        ]
