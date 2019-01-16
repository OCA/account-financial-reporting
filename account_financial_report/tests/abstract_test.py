# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests import common
from odoo.tools import test_reports

_logger = logging.getLogger(__name__)


class AbstractTest(common.TransactionCase):
    """Common technical tests for all reports."""
    at_install = False
    post_install = True

    accounts = {}

    def with_context(self, *args, **kwargs):
        context = dict(args[0] if args else self.env.context, **kwargs)
        self.env = self.env(context=context)
        return self

    def _chart_template_create(self):
        transfer_account_id = self.env['account.account.template'].create({
            'code': '000',
            'name': 'Liquidity Transfers',
            'reconcile': True,
            'user_type_id': self.ref(
                "account.data_account_type_current_assets"),
        })
        self.chart = self.env['account.chart.template'].create({
            'name': 'Test COA',
            'code_digits': 4,
            'bank_account_code_prefix': 1014,
            'cash_account_code_prefix': 1014,
            'currency_id': self.ref('base.USD'),
            'transfer_account_code_prefix': '000',
        })
        transfer_account_id.update({
            'chart_template_id': self.chart.id,
        })
        self.env['ir.model.data'].create({
            'res_id': transfer_account_id.id,
            'model': transfer_account_id._name,
            'name': 'Liquidity Transfers',
        })
        act = self.env['account.account.template'].create({
            'code': '001',
            'name': 'Expenses',
            'user_type_id': self.ref("account.data_account_type_expenses"),
            'chart_template_id': self.chart.id,
            'reconcile': True,
        })
        self.env['ir.model.data'].create({
            'res_id': act.id,
            'model': act._name,
            'name': 'expenses',
        })
        act = self.env['account.account.template'].create({
            'code': '002',
            'name': 'Product Sales',
            'user_type_id': self.ref("account.data_account_type_revenue"),
            'chart_template_id': self.chart.id,
            'reconcile': True,
        })
        self.env['ir.model.data'].create({
            'res_id': act.id,
            'model': act._name,
            'name': 'sales',
        })
        act = self.env['account.account.template'].create({
            'code': '003',
            'name': 'Account Receivable',
            'user_type_id': self.ref("account.data_account_type_receivable"),
            'chart_template_id': self.chart.id,
            'reconcile': True,
        })
        self.env['ir.model.data'].create({
            'res_id': act.id,
            'model': act._name,
            'name': 'receivable',
        })
        act = self.env['account.account.template'].create({
            'code': '004',
            'name': 'Account Payable',
            'user_type_id': self.ref("account.data_account_type_payable"),
            'chart_template_id': self.chart.id,
            'reconcile': True,
        })
        self.env['ir.model.data'].create({
            'res_id': act.id,
            'model': act._name,
            'name': 'payable',
        })

    def _add_chart_of_accounts(self):
        self.company = self.env['res.company'].create({
            'name': 'Spanish test company',
        })
        self.env.ref('base.group_multi_company').write({
            'users': [(4, self.env.uid)],
        })
        self.env.user.write({
            'company_ids': [(4, self.company.id)],
            'company_id': self.company.id,
        })
        self.with_context(
            company_id=self.company.id, force_company=self.company.id)
        self.chart.try_loading_for_current_company()
        self.revenue = self.env['account.account'].search(
            [('user_type_id', '=', self.ref(
                "account.data_account_type_revenue"))], limit=1)
        self.expense = self.env['account.account'].search(
            [('user_type_id', '=', self.ref(
                "account.data_account_type_expenses"))], limit=1)
        self.receivable = self.env['account.account'].search(
            [('user_type_id', '=', self.ref(
                "account.data_account_type_receivable"))], limit=1)
        self.payable = self.env['account.account'].search(
            [('user_type_id', '=', self.ref(
                "account.data_account_type_payable"))], limit=1)
        return True

    def _journals_create(self):
        self.journal_sale = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.revenue.id,
            'default_credit_account_id': self.revenue.id,
        })
        self.journal_purchase = self.env['account.journal'].create({
            'company_id': self.company.id,
            'name': 'Test journal for purchase',
            'type': 'purchase',
            'code': 'TPUR',
            'default_debit_account_id': self.expense.id,
            'default_credit_account_id': self.expense.id,
        })
        return True

    def _invoice_create(self):
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'company_id': self.company.id,
            'property_account_receivable_id': self.receivable.id,
            'property_account_payable_id': self.payable.id,
        })

        # customer invoice
        customer_invoice_lines = [(0, False, {
            'name': 'Test description #1',
            'account_id': self.revenue.id,
            'quantity': 1.0,
            'price_unit': 100.0,
        }), (0, False, {
            'name': 'Test description #2',
            'account_id': self.revenue.id,
            'quantity': 2.0,
            'price_unit': 25.0,
        })]
        self.invoice_out = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
            'invoice_line_ids': customer_invoice_lines,
            'account_id': self.partner.property_account_receivable_id.id,
            'journal_id': self.journal_sale.id,
        })
        self.invoice_out.action_invoice_open()

        # vendor bill
        vendor_invoice_lines = [(0, False, {
            'name': 'Test description #1',
            'account_id': self.revenue.id,
            'quantity': 1.0,
            'price_unit': 100.0,
        }), (0, False, {
            'name': 'Test description #2',
            'account_id': self.revenue.id,
            'quantity': 2.0,
            'price_unit': 25.0,
        })]
        self.invoice_in = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'invoice_line_ids': vendor_invoice_lines,
            'account_id': self.partner.property_account_payable_id.id,
            'journal_id': self.journal_purchase.id,
        })
        self.invoice_in.action_invoice_open()

    def setUp(self):
        super(AbstractTest, self).setUp()

        self.with_context()
        self._chart_template_create()
        self._add_chart_of_accounts()
        self._journals_create()
        self._invoice_create()

        self.model = self._getReportModel()

        self.qweb_report_name = self._getQwebReportName()
        self.xlsx_report_name = self._getXlsxReportName()
        self.xlsx_action_name = self._getXlsxReportActionName()

        self.report_title = self._getReportTitle()

        self.base_filters = self._getBaseFilters()
        self.additional_filters = self._getAdditionalFiltersToBeTested()

        self.report = self.model.create(self.base_filters)
        self.report.compute_data_for_report()

    def test_html(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.qweb_report_name,
                                [self.report.id],
                                report_type='qweb-html')

    def test_qweb(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.qweb_report_name,
                                [self.report.id],
                                report_type='qweb-pdf')

    def test_xlsx(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.xlsx_report_name,
                                [self.report.id],
                                report_type='xlsx')

    def test_print(self):
        self.report.print_report('qweb')
        self.report.print_report('xlsx')

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
            report_accounts = report.account_ids.filtered('account_id')
            current_filter.update({
                'filter_account_ids':
                    [(6, 0, report_accounts[0].account_id.ids)],
            })

            report2 = self.model.create(current_filter)
            report2.compute_data_for_report()

            self.assertEqual(len(report2.account_ids), 1)
            self.assertEqual(report2.account_ids.name,
                             report_accounts[0].name)

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
