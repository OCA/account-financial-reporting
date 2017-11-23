
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
import logging
_logger = logging.getLogger(__name__)

try:
    from xlrd import open_workbook
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')


class AbstractTest(TransactionCase):
    """Common technical tests for all reports."""

    def setUp(cls):
        super(AbstractTest, cls).setUp()

        cls.model = cls._getReportModel()

        cls.qweb_report_name = cls._getQwebReportName()
        cls.xlsx_report_name = cls._getXlsxReportName()
        cls.xlsx_action_name = cls._getXlsxReportActionName()

        cls.report_title = cls._getReportTitle()

        cls.base_filters = cls._getBaseFilters()
        cls.additional_filters = cls._getAdditionalFiltersToBeTested()

        cls.report = cls.model.create(cls.base_filters)
        cls.report.compute_data_for_report()

    def test_01_generation_report_qweb(self):
        """Check if report PDF/HTML is correctly generated"""

        # Check if returned report action is correct
        report_type = 'qweb-pdf'
        report_action = self.report.print_report(report_type)
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report',
                'report_name': self.qweb_report_name,
                'report_type': 'qweb-pdf',
            },
            report_action
        )

        # Check if report template is correct
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', self.qweb_report_name),
             ('report_type', '=', report_type)], limit=1)
        self.assertEqual(report.report_type, 'qweb-pdf')

        rep = report.render(self.report.ids, {})

        self.assertTrue(self.report_title.encode('utf8') in rep[0])

        self.assertTrue(
            self.report.account_ids[0].name.encode('utf8') in rep[0]
        )

    def test_02_generation_report_html(self):
        """Check if report HTML is correctly generated"""

        # Check if returned report action is correct
        report_type = 'qweb-html'
        report_action = self.report.print_report(report_type)
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report',
                'report_name': self.qweb_report_name,
                'report_type': 'qweb-html',
            },
            report_action
        )

        # Check if report template is correct
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', self.qweb_report_name),
             ('report_type', '=', report_type)], limit=1)
        self.assertEqual(report.report_type, 'qweb-html')

        rep = report.render(self.report.ids, {})

        self.assertTrue(self.report_title.encode('utf8') in rep[0])
        self.assertTrue(
            self.report.account_ids[0].name.encode('utf8') in rep[0]
        )

    def test_03_generation_report_xlsx(self):
        """Check if report XLSX is correctly generated"""
        report_object = self.env['ir.actions.report']
        # Check if returned report action is correct
        report_type = 'xlsx'
        report_action = self.report.print_report(report_type)
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report',
                'report_name': self.xlsx_report_name,
                'report_type': 'xlsx',
            },
            report_action
        )
        report = report_object._get_report_from_name(self.xlsx_report_name)
        self.assertEqual(report.report_type, 'xlsx')
        report_xlsx = report.render(self.report.ids, {})
        wb = open_workbook(file_contents=report_xlsx[0])
        sheet = wb.sheet_by_index(0)
        class_name = 'report.%s' % report.report_name
        self.assertEqual(sheet.cell(0, 0).value,
                         self.env[class_name]._get_report_name())

    def test_04_compute_data(self):
        """Check that the SQL queries work with all filters options"""

        for filters in [{}] + self.additional_filters:
            current_filter = self.base_filters.copy()
            current_filter.update(filters)

            report = self.model.create(current_filter)
            report.compute_data_for_report()

            self.assertGreaterEqual(len(report.account_ids), 1)

            # Same filters with only one account
            current_filter = self.base_filters.copy()
            current_filter.update(filters)
            current_filter.update({
                'filter_account_ids':
                    [(6, 0, report.account_ids[0].account_id.ids)],
            })

            report2 = self.model.create(current_filter)
            report2.compute_data_for_report()

            self.assertEqual(len(report2.account_ids), 1)
            self.assertEqual(report2.account_ids.name,
                             report.account_ids[0].name)

            if self._partner_test_is_possible(filters):
                # Same filters with only one partner
                report_partner_ids = report.account_ids.mapped('partner_ids')
                partner_ids = report_partner_ids.mapped('partner_id')

                current_filter = self.base_filters.copy()
                current_filter.update(filters)
                current_filter.update({
                    'filter_partner_ids': [(6, 0, partner_ids[0].ids)],
                })

                report3 = self.model.create(current_filter)
                report3.compute_data_for_report()

                self.assertGreaterEqual(len(report3.account_ids), 1)

                report_partner_ids3 = report3.account_ids.mapped('partner_ids')
                partner_ids3 = report_partner_ids3.mapped('partner_id')

                self.assertEqual(len(partner_ids3), 1)
                self.assertEqual(
                    partner_ids3.name,
                    partner_ids[0].name
                )

                # Same filters with only one partner and one account
                report_partner_ids = report3.account_ids.mapped('partner_ids')
                report_account_id = report_partner_ids.filtered(
                    lambda p: p.partner_id
                )[0].report_account_id

                current_filter = self.base_filters.copy()
                current_filter.update(filters)
                current_filter.update({
                    'filter_account_ids':
                        [(6, 0, report_account_id.account_id.ids)],
                    'filter_partner_ids': [(6, 0, partner_ids[0].ids)],
                })

                report4 = self.model.create(current_filter)
                report4.compute_data_for_report()

                self.assertEqual(len(report4.account_ids), 1)
                self.assertEqual(report4.account_ids.name,
                                 report_account_id.account_id.name)

                report_partner_ids4 = report4.account_ids.mapped('partner_ids')
                partner_ids4 = report_partner_ids4.mapped('partner_id')

                self.assertEqual(len(partner_ids4), 1)
                self.assertEqual(
                    partner_ids4.name,
                    partner_ids[0].name
                )

    def _partner_test_is_possible(self, filters):
        """
            :return:
                a boolean to indicate if partner test is possible
                with current filters
        """
        return True

    def _getReportModel(self):
        """
            :return: the report model name
        """
        raise NotImplementedError()

    def _getQwebReportName(self):
        """
            :return: the qweb report name
        """
        raise NotImplementedError()

    def _getXlsxReportName(self):
        """
            :return: the xlsx report name
        """
        raise NotImplementedError()

    def _getXlsxReportActionName(self):
        """
            :return: the xlsx report action name
        """
        raise NotImplementedError()

    def _getReportTitle(self):
        """
            :return: the report title displayed into the report
        """
        raise NotImplementedError()

    def _getBaseFilters(self):
        """
            :return: the minimum required filters to generate report
        """
        raise NotImplementedError()

    def _getAdditionalFiltersToBeTested(self):
        """
            :return: the additional filters to generate report variants
        """
        raise NotImplementedError()
