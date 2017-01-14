# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .test_common_xls import TestCommonXls


class TestTrialBalanceXls(TestCommonXls):

    def _getReportModel(self):
        return 'trial.balance.webkit'

    def _getXlsReportName(self):
        return 'account.account_report_trial_balance_xls'

    def _getXlsReportActionName(self):
        module = 'account_financial_report_webkit'
        action = 'account_report_trial_balance_webkit'
        return '%s.%s' % (module, action)

    def _getBaseFilters(self):
        return {}

    def test_common(self):
        common_tests = [
            x for x in dir(self)
            if callable(getattr(self, x)) and x.startswith('common_test_')]
        for test in common_tests:
            getattr(self, test)()
