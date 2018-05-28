# -*- coding: utf-8 -*-
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from . import abstract_test_foreign_currency as a_t_f_c


class TestOpenItems(a_t_f_c.AbstractTestForeignCurrency):
    """
        Technical tests for Open Items Report.
    """

    def _getReportModel(self):
        return self.env['report_open_items_qweb']

    def _getQwebReportName(self):
        return 'account_financial_report_qweb.report_open_items_qweb'

    def _getXlsxReportName(self):
        return 'account_financial_report_qweb.report_open_items_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report_qweb.action_report_open_items_xlsx'

    def _getReportTitle(self):
        return 'Open Items'

    def _getBaseFilters(self):
        return {
            'date_at': time.strftime('%Y-12-31'),
            'company_id': self.company.id,
            'foreign_currency': True,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'only_posted_moves': True},
            {'hide_account_balance_at_0': True},
            {'only_posted_moves': True, 'hide_account_balance_at_0': True},
        ]
