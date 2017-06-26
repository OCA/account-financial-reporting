# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.tests.common import TransactionCase


class TestCommon(TransactionCase):
    """ Common tests for all reports """

    def setUp(self):
        super(TestCommon, self).setUp()
        self.model = self.env[self._getReportModel()]
        self.report_name = self._getReportName()
        wiz_vals = {'chart_account_id': self.env.ref('account.chart0').id}
        wiz_vals.update(self._getBaseFilters())
        self.report = self.model.create(wiz_vals)

    def common_test_01_generation_report(self):
        """ Check if report is correctly generated """

        # Check if returned report action is correct
        report_action = self.report.check_report()
        self.assertDictContainsSubset(
            {'type': 'ir.actions.report.xml',
             'report_name': self.report_name},
            report_action)

    def _getReportModel(self):
        """
            :return: the report model name
        """
        raise NotImplementedError()

    def _getReportName(self):
        """
            :return: the xls report name
        """
        raise NotImplementedError()

    def _getBaseFilters(self):
        """
            :return: the minimum required filters to generate report
        """
        raise NotImplementedError()
