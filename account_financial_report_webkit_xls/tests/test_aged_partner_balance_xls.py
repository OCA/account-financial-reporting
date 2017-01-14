# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .test_common_xls import TestCommonXls


class TestAgedPartnerBalanceXls(TestCommonXls):

    def _getReportModel(self):
        return 'account.aged.trial.balance.webkit'

    def _getXlsReportName(self):
        return 'account.account_report_aged_partner_balance_xls'

    def _getXlsReportActionName(self):
        module = 'account_financial_report_webkit'
        action = 'account_report_aged_trial_blanance_webkit'
        return '%s.%s' % (module, action)

    def _getBaseFilters(self):
        fy_id = self.model._get_current_fiscalyear()
        vals = self.model.onchange_fiscalyear(fiscalyear=fy_id)['value']
        vals.update({'fiscalyear_id': fy_id})
        return vals

    def test_common(self):
        common_tests = [
            x for x in dir(self)
            if callable(getattr(self, x)) and x.startswith('common_test_')]
        for test in common_tests:
            getattr(self, test)()
