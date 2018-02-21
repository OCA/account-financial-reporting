# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .test_common import TestCommon


class TestGeneralLedger(TestCommon):

    def _getReportModel(self):
        return 'print.journal.webkit'

    def _getReportName(self):
        return 'account.account_report_print_journal_webkit'

    def _getBaseFilters(self):
        fy_id = self.model._get_fiscalyear()
        vals = self.model.onchange_filter(
            filter='filter_period', fiscalyear_id=fy_id)['value']
        vals.update({'fiscalyear_id': fy_id})
        return vals

    def test_common(self):
        common_tests = [
            x for x in dir(self)
            if callable(getattr(self, x)) and x.startswith('common_test_')]
        for test in common_tests:
            getattr(self, test)()
