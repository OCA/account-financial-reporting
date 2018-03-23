# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo.tests import common
from . import abstract_test_tax_report


class TestVAT(abstract_test_tax_report.AbstractTest):
    """
        Technical tests for VAT Report.
    """

    def _getReportModel(self):
        return self.env['report_vat_report']

    def _getQwebReportName(self):
        return 'account_financial_report.report_vat_report_qweb'

    def _getXlsxReportName(self):
        return 'a_f_r.report_vat_report_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report.action_report_vat_report_xlsx'

    def _getReportTitle(self):
        return 'Odoo'

    def _getBaseFilters(self):
        return {
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'company_id': self.env.user.company_id.id,
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'based_on': 'taxtags'},
            {'based_on': 'taxgroups'},
            {'tax_details': True},
            {'based_on': 'taxtags', 'tax_details': True},
            {'based_on': 'taxgroups', 'tax_details': True},
        ]


class TestVATReport(common.TransactionCase):

    def setUp(self):
        super(TestVATReport, self).setUp()
        self.date_from = time.strftime('%Y-%m-01')
        self.date_to = time.strftime('%Y-%m-28')
        self.company = self.env.ref('base.main_company')
        self.receivable_account = self.env['account.account'].search([
            ('company_id', '=', self.company.id),
            ('user_type_id.name', '=', 'Receivable')
            ], limit=1)
        self.income_account = self.env['account.account'].search([
            ('company_id', '=', self.company.id),
            ('user_type_id.name', '=', 'Income')
            ], limit=1)
        self.tax_account = self.env['account.account'].search([
            ('company_id', '=', self.company.id),
            ('user_type_id',
             '=',
             self.env.ref(
                 'account.data_account_type_non_current_liabilities').id)
            ], limit=1)
        self.bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'), ('company_id', '=', self.company.id)
            ], limit=1)
        self.tax_tag_01 = self.env['account.account.tag'].create({
            'name': 'Tag 01',
            'applicability': 'taxes'
        })
        self.tax_tag_02 = self.env['account.account.tag'].create({
            'name': 'Tag 02',
            'applicability': 'taxes'
        })
        self.tax_tag_03 = self.env['account.account.tag'].create({
            'name': 'Tag 03',
            'applicability': 'taxes'
        })
        self.tax_group_10 = self.env['account.tax.group'].create({
            'name': 'Tax 10%',
            'sequence': 1
        })
        self.tax_group_20 = self.env['account.tax.group'].create({
            'name': 'Tax 20%',
            'sequence': 2
        })
        self.tax_10 = self.env['account.tax'].create({
            'name': 'Tax 10.0%',
            'amount': 10.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'account_id': self.tax_account.id,
            'company_id': self.company.id,
            'refund_account_id': self.tax_account.id,
            'tax_group_id': self.tax_group_10.id,
            'tag_ids': [(6, 0, [self.tax_tag_01.id, self.tax_tag_02.id])]
        })
        self.tax_20 = self.env['account.tax'].create({
            'sequence': 30,
            'name': 'Tax 20.0%',
            'amount': 20.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'tax_exigibility': 'on_payment',
            'account_id': self.tax_account.id,
            'company_id': self.company.id,
            'refund_account_id': self.tax_account.id,
            'cash_basis_account': self.tax_account.id,
            'tax_group_id': self.tax_group_20.id,
            'tag_ids': [(6, 0, [self.tax_tag_02.id, self.tax_tag_03.id])]
        })

        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.receivable_account.id,
            'company_id': self.company.id,
            'date_invoice': time.strftime('%Y-%m-03'),
            'type': 'out_invoice',
        })

        self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_4').id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': invoice.id,
            'name': 'product',
            'account_id': self.income_account.id,
            'invoice_line_tax_ids': [(6, 0, [self.tax_10.id])],
        })
        invoice.compute_taxes()
        invoice.action_invoice_open()

        self.cbinvoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.receivable_account.id,
            'company_id': self.company.id,
            'date_invoice': time.strftime('%Y-%m-05'),
            'type': 'out_invoice',
        })

        self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_4').id,
            'quantity': 1.0,
            'price_unit': 500.0,
            'invoice_id': self.cbinvoice.id,
            'name': 'product',
            'account_id': self.income_account.id,
            'invoice_line_tax_ids': [(6, 0, [self.tax_20.id])],
        })
        self.cbinvoice.compute_taxes()
        self.cbinvoice.action_invoice_open()

    def _get_report_lines(self):
        self.cbinvoice.pay_and_reconcile(
            self.bank_journal.id, 300, time.strftime('%Y-%m-10'))
        vat_report = self.env['report_vat_report'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company.id,
            'based_on': 'taxtags',
            'tax_detail': True,
            })
        vat_report.compute_data_for_report()
        lines = {}
        vat_taxtag_model = self.env['report_vat_report_taxtag']
        lines['tag_01'] = vat_taxtag_model.search([
            ('report_id', '=', vat_report.id),
            ('taxtag_id', '=', self.tax_tag_01.id),
        ])
        lines['tag_02'] = vat_taxtag_model.search([
            ('report_id', '=', vat_report.id),
            ('taxtag_id', '=', self.tax_tag_02.id),
        ])
        lines['tag_03'] = vat_taxtag_model.search([
            ('report_id', '=', vat_report.id),
            ('taxtag_id', '=', self.tax_tag_03.id),
        ])
        vat_tax_model = self.env['report_vat_report_tax']
        lines['tax_10'] = vat_tax_model.search([
            ('report_tax_id', '=', lines['tag_02'].id),
            ('tax_id', '=', self.tax_10.id),
        ])
        lines['tax_20'] = vat_tax_model.search([
            ('report_tax_id', '=', lines['tag_02'].id),
            ('tax_id', '=', self.tax_20.id),
        ])
        vat_report['based_on'] = 'taxgroups'
        vat_report.compute_data_for_report()
        lines['group_10'] = vat_taxtag_model.search([
            ('report_id', '=', vat_report.id),
            ('taxgroup_id', '=', self.tax_group_10.id),
        ])
        lines['group_20'] = vat_taxtag_model.search([
            ('report_id', '=', vat_report.id),
            ('taxgroup_id', '=', self.tax_group_20.id),
        ])
        vat_tax_model = self.env['report_vat_report_tax']
        lines['tax_group_10'] = vat_tax_model.search([
            ('report_tax_id', '=', lines['group_10'].id),
            ('tax_id', '=', self.tax_10.id),
        ])
        lines['tax_group_20'] = vat_tax_model.search([
            ('report_tax_id', '=', lines['group_20'].id),
            ('tax_id', '=', self.tax_20.id),
        ])
        return lines

    def test_01_compute(self):
        # Generate the vat lines
        lines = self._get_report_lines()

        # Check report based on taxtags
        self.assertEqual(len(lines['tag_01']), 1)
        self.assertEqual(len(lines['tag_02']), 1)
        self.assertEqual(len(lines['tag_03']), 1)
        self.assertEqual(len(lines['tax_10']), 1)
        self.assertEqual(len(lines['tax_20']), 1)
        self.assertEqual(lines['tag_01'].net, 100)
        self.assertEqual(lines['tag_01'].tax, 10)
        self.assertEqual(lines['tag_02'].net, 350)
        self.assertEqual(lines['tag_02'].tax, 60)
        self.assertEqual(lines['tag_03'].net, 250)
        self.assertEqual(lines['tag_03'].tax, 50)
        self.assertEqual(lines['tax_10'].net, 100)
        self.assertEqual(lines['tax_10'].tax, 10)
        self.assertEqual(lines['tax_20'].net, 250)
        self.assertEqual(lines['tax_20'].tax, 50)

        # Check report based on taxgroups
        self.assertEqual(len(lines['group_10']), 1)
        self.assertEqual(len(lines['group_20']), 1)
        self.assertEqual(len(lines['tax_group_10']), 1)
        self.assertEqual(len(lines['tax_group_20']), 1)
        self.assertEqual(lines['group_10'].net, 100)
        self.assertEqual(lines['group_10'].tax, 10)
        self.assertEqual(lines['group_20'].net, 250)
        self.assertEqual(lines['group_20'].tax, 50)
        self.assertEqual(lines['tax_group_10'].net, 100)
        self.assertEqual(lines['tax_group_10'].tax, 10)
        self.assertEqual(lines['tax_group_20'].net, 250)
        self.assertEqual(lines['tax_group_20'].tax, 50)

    def test_get_report_html(self):
        vat_report = self.env['report_vat_report'].create({
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_id': self.company.id,
            'tax_detail': True,
            })
        vat_report.compute_data_for_report()
        vat_report.get_html(given_context={})

    def test_wizard_date_range(self):
        vat_wizard = self.env['vat.report.wizard']
        date_range = self.env['date.range']
        self.type = self.env['date.range.type'].create(
            {'name': 'Month',
             'company_id': False,
             'allow_overlap': False})
        dt = date_range.create({
            'name': 'FS2016',
            'date_start': time.strftime('%Y-%m-01'),
            'date_end': time.strftime('%Y-%m-28'),
            'type_id': self.type.id,
        })
        wizard = vat_wizard.create(
            {'date_range_id': dt.id,
             'date_from': time.strftime('%Y-%m-28'),
             'date_to': time.strftime('%Y-%m-01'),
             'tax_detail': True})
        wizard.onchange_date_range_id()
        self.assertEqual(wizard.date_from, time.strftime('%Y-%m-01'))
        self.assertEqual(wizard.date_to, time.strftime('%Y-%m-28'))
        wizard._export('qweb-pdf')
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
        wizard = vat_wizard.create(
            {'date_range_id': dt.id,
             'date_from': time.strftime('%Y-%m-28'),
             'date_to': time.strftime('%Y-%m-01'),
             'based_on': 'taxgroups',
             'tax_detail': True})
        wizard.onchange_date_range_id()
        self.assertEqual(wizard.date_from, time.strftime('%Y-%m-01'))
        self.assertEqual(wizard.date_to, time.strftime('%Y-%m-28'))
        wizard._export('qweb-pdf')
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
