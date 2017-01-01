# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.tests.common import TransactionCase


class TestCommonXls(TransactionCase):
    """ Common tests for all XLS Exports """

    def setUp(self):
        super(TestCommonXls, self).setUp()
        self.model = self.env[self._getReportModel()]
        self.xls_report_name = self._getXlsReportName()
        wiz_vals = {'chart_account_id': self.env.ref('account.chart0').id}
        wiz_vals.update(self._getBaseFilters())
        ctx = {'xls_export': 1}
        self.report = self.model.with_context(ctx).create(wiz_vals)

    def common_test_01_generation_report_xls(self):
        """ Check if report XLS is correctly generated """

        # Check if returned report action is correct
        report_action = self.report.xls_export()
        self.assertDictContainsSubset(
            {'type': 'ir.actions.report.xml',
             'report_name': self.xls_report_name},
            report_action)

    def _getReportModel(self):
        """
            :return: the report model name
        """
        raise NotImplementedError()

    def _getXlsReportName(self):
        """
            :return: the xls report name
        """
        raise NotImplementedError()

    def _getBaseFilters(self):
        """
            :return: the minimum required filters to generate report
        """
        raise NotImplementedError()
