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
        ctx = {'xls_export': 1}
        self.xls_action_name = self._getXlsReportActionName()
        self.xls_action = self.env.ref(self.xls_action_name).with_context(ctx)
        wiz_vals = {'chart_account_id': self.env.ref('account.chart0').id}
        wiz_vals.update(self._getBaseFilters())
        self.report = self.model.with_context(ctx).create(wiz_vals)

    def common_test_01_action_xls(self):
        """ Check if report XLS action is correct """
        report_action = self.report.xls_export()
        self.assertDictContainsSubset(
            {'type': 'ir.actions.report.xml',
             'report_name': self.xls_report_name},
            report_action)
        self.render_dict = report_action['datas']

    def common_test_02_render_xls(self):
        report_xls = self.xls_action.render_report(
            self.report.ids,
            self.xls_report_name,
            self.render_dict)
        self.assertGreaterEqual(len(report_xls[0]), 1)
        self.assertEqual(report_xls[1], 'xls')

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

    def _getXlsReportActionName(self):
        """
            :return: the xls report action name
        """
        raise NotImplementedError()

    def _getBaseFilters(self):
        """
            :return: the minimum required filters to generate report
        """
        raise NotImplementedError()
