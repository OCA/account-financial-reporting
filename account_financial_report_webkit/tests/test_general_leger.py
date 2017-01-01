# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from .test_common import TestCommon


class TestGeneralLedger(TestCommon):

    def _getReportModel(self):
        return 'general.ledger.webkit'

    def _getReportName(self):
        return 'account.account_report_general_ledger_webkit'

    def _getBaseFilters(self):
        return {}

    def test_common(self):
        common_tests = [
            x for x in dir(self)
            if callable(getattr(self, x)) and x.startswith('common_test_')]
        for test in common_tests:
            getattr(self, test)()
