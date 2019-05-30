# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from odoo.fields import Date
from odoo.tests.common import TransactionCase

from . import abstract_test_foreign_currency as a_t_f_c


class TestJournalLedger(a_t_f_c.AbstractTestForeignCurrency):
    """
        Technical tests for General Ledger Report.
    """
    def _getReportModel(self):
        return self.env['report_journal_ledger']

    def _getQwebReportName(self):
        return 'account_financial_report.report_journal_ledger_qweb'

    def _getXlsxReportName(self):
        return 'a_f_r.report_journal_ledger_xlsx'

    def _getXlsxReportActionName(self):
        return 'account_financial_report.' \
               'action_report_journal_ledger_xlsx'

    def _getReportTitle(self):
        return 'Odoo'

    def _getBaseFilters(self):
        return {
            'date_from': date(date.today().year, 1, 1),
            'date_to': date(date.today().year, 12, 31),
            'company_id': self.company.id,
            'journal_ids': [(6, 0, self.journal_sale.ids)]
        }

    def _getAdditionalFiltersToBeTested(self):
        return [
            {'move_target': "All",
             'sort_option': "Date",
             'group_option': "Journal",
             'with_account_name': True,
             'foreign_currency': True},
        ]

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
            self.report.journal_ids[0].name.encode('utf8') in rep[0]
        )

    def test_04_compute_data(self):
        return True


class TestJournalReport(TransactionCase):

    def setUp(self):
        super(TestJournalReport, self).setUp()
        self.AccountObj = self.env['account.account']
        self.InvoiceObj = self.env['account.invoice']
        self.JournalObj = self.env['account.journal']
        self.JournalReportObj = self.env['journal.ledger.report.wizard']
        self.MoveObj = self.env['account.move']
        self.ReportJournalLedger = self.env['report_journal_ledger']
        self.TaxObj = self.env['account.tax']

        self.company = self.env.ref('base.main_company')

        today = datetime.today()
        last_year = today - relativedelta(years=1)

        self.previous_fy_date_start = Date.to_string(
            last_year.replace(month=1, day=1))
        self.previous_fy_date_end = Date.to_string(
            last_year.replace(month=12, day=31))
        self.fy_date_start = Date.to_string(
            today.replace(month=1, day=1))
        self.fy_date_end = Date.to_string(
            today.replace(month=12, day=31))

        self.receivable_account = self.AccountObj.search([
            ('user_type_id.name', '=', 'Receivable')
        ], limit=1)
        self.income_account = self.AccountObj.search([
            ('user_type_id.name', '=', 'Income')
        ], limit=1)
        self.payable_account = self.AccountObj.search([
            ('user_type_id.name', '=', 'Payable')
        ], limit=1)

        self.journal_sale = self.JournalObj.create({
            'name': "Test journal sale",
            'code': "TST-JRNL-S",
            'type': 'sale',
            'company_id': self.company.id,
        })
        self.journal_purchase = self.JournalObj.create({
            'name': "Test journal purchase",
            'code': "TST-JRNL-P",
            'type': 'sale',
            'company_id': self.company.id,
        })

        self.tax_15_s = self.TaxObj.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 15.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'sale',
        })

        self.tax_20_s = self.TaxObj.create({
            'sequence': 30,
            'name': 'Tax 20.0% (Percentage of Price)',
            'amount': 20.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'sale',
        })

        self.tax_15_p = self.TaxObj.create({
            'sequence': 30,
            'name': 'Tax 15.0% (Percentage of Price)',
            'amount': 15.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
        })

        self.tax_20_p = self.TaxObj.create({
            'sequence': 30,
            'name': 'Tax 20.0% (Percentage of Price)',
            'amount': 20.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'purchase',
        })

        self.partner_2 = self.env.ref('base.res_partner_2')

    def _add_move(
            self, date, journal,
            receivable_debit, receivable_credit, income_debit, income_credit):
        move_name = 'move name'
        move_vals = {
            'journal_id': journal.id,
            'date': date,
            'line_ids': [
                (0, 0, {
                    'name': move_name,
                    'debit': receivable_debit,
                    'credit': receivable_credit,
                    'account_id': self.receivable_account.id
                }),
                (0, 0, {
                    'name': move_name,
                    'debit': income_debit,
                    'credit': income_credit,
                    'account_id': self.income_account.id
                }),
            ]
        }
        return self.MoveObj.create(move_vals)

    def check_report_journal_debit_credit(
            self, report, expected_debit, expected_credit):
        self.assertEqual(
            expected_debit,
            sum([journal.debit for journal in
                 report.report_journal_ledger_ids])
        )

        self.assertEqual(
            expected_credit,
            sum([journal.credit for journal in
                 report.report_journal_ledger_ids])
        )

    def check_report_journal_debit_credit_taxes(
            self, report,
            expected_base_debit, expected_base_credit,
            expected_tax_debit, expected_tax_credit):

        self.assertEqual(
            expected_base_debit,
            sum([
                journal.base_debit
                for journal in report.report_journal_ledger_tax_line_ids
            ])
        )
        self.assertEqual(
            expected_base_credit,
            sum([
                journal.base_credit
                for journal in report.report_journal_ledger_tax_line_ids
            ])
        )
        self.assertEqual(
            expected_tax_debit,
            sum([
                journal.tax_debit
                for journal in report.report_journal_ledger_tax_line_ids
            ])
        )
        self.assertEqual(
            expected_tax_credit,
            sum([
                journal.tax_credit
                for journal in report.report_journal_ledger_tax_line_ids
            ])
        )

    def test_01_test_total(self):
        today_date = Date.today()
        last_year_date = Date.to_string(
            datetime.today() - relativedelta(years=1))

        move1 = self._add_move(
            today_date, self.journal_sale,
            0, 100, 100, 0)
        move2 = self._add_move(
            last_year_date, self.journal_sale,
            0, 100, 100, 0)

        report = self.ReportJournalLedger.create({
            'date_from': self.fy_date_start,
            'date_to': self.fy_date_end,
            'company_id': self.company.id,
            'journal_ids': [(6, 0, self.journal_sale.ids)]
        })
        report.compute_data_for_report()

        self.check_report_journal_debit_credit(report, 100, 100)

        move3 = self._add_move(
            today_date, self.journal_sale,
            0, 100, 100, 0)

        report.compute_data_for_report()
        self.check_report_journal_debit_credit(report, 200, 200)

        report.move_target = 'posted'
        report.compute_data_for_report()
        self.check_report_journal_debit_credit(report, 0, 0)

        move1.post()
        report.compute_data_for_report()
        self.check_report_journal_debit_credit(report, 100, 100)

        move2.post()
        report.compute_data_for_report()
        self.check_report_journal_debit_credit(report, 100, 100)

        move3.post()
        report.compute_data_for_report()
        self.check_report_journal_debit_credit(report, 200, 200)

        report.date_from = self.previous_fy_date_start
        report.compute_data_for_report()
        self.check_report_journal_debit_credit(report, 300, 300)

    def test_02_test_taxes_out_invoice(self):
        invoice_values = {
            'journal_id': self.journal_sale.id,
            'partner_id': self.partner_2.id,
            'type': 'out_invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'quantity': 1.0,
                    'price_unit': 100,
                    'account_id': self.receivable_account.id,
                    'name': "Test",
                    'invoice_line_tax_ids': [(6, 0, [self.tax_15_s.id])],
                }),
                (0, 0, {
                    'quantity': 1.0,
                    'price_unit': 100,
                    'account_id': self.receivable_account.id,
                    'name': "Test",
                    'invoice_line_tax_ids': [(6, 0, [
                        self.tax_15_s.id, self.tax_20_s.id
                    ])],
                })
            ]
        }
        invoice = self.InvoiceObj.create(invoice_values)
        invoice.action_invoice_open()

        report = self.ReportJournalLedger.create({
            'date_from': self.fy_date_start,
            'date_to': self.fy_date_end,
            'company_id': self.company.id,
            'journal_ids': [(6, 0, self.journal_sale.ids)]
        })
        report.compute_data_for_report()

        self.check_report_journal_debit_credit(report, 250, 250)
        self.check_report_journal_debit_credit_taxes(report, 0, 300, 0, 50)

    def test_03_test_taxes_in_invoice(self):
        invoice_values = {
            'journal_id': self.journal_sale.id,
            'partner_id': self.partner_2.id,
            'type': 'in_invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'quantity': 1.0,
                    'price_unit': 100,
                    'account_id': self.payable_account.id,
                    'name': "Test",
                    'invoice_line_tax_ids': [(6, 0, [self.tax_15_p.id])],
                }),
                (0, 0, {
                    'quantity': 1.0,
                    'price_unit': 100,
                    'account_id': self.payable_account.id,
                    'name': "Test",
                    'invoice_line_tax_ids': [(6, 0, [
                        self.tax_15_p.id, self.tax_20_p.id
                    ])],
                })
            ]
        }
        invoice = self.InvoiceObj.create(invoice_values)
        invoice.action_invoice_open()

        report = self.ReportJournalLedger.create({
            'date_from': self.fy_date_start,
            'date_to': self.fy_date_end,
            'company_id': self.company.id,
            'journal_ids': [(6, 0, self.journal_sale.ids)]
        })
        report.compute_data_for_report()

        self.check_report_journal_debit_credit(report, 250, 250)
        self.check_report_journal_debit_credit_taxes(report, 300, 0, 50, 0)
