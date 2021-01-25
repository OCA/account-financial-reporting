# Copyright 2017 ACSONE SA/NV
# Copyright 2019-20 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.fields import Date
from odoo.tests.common import Form, TransactionCase


class TestJournalReport(TransactionCase):
    def setUp(self):
        super(TestJournalReport, self).setUp()
        self.AccountObj = self.env["account.account"]
        self.InvoiceObj = self.env["account.move"]
        self.JournalObj = self.env["account.journal"]
        self.MoveObj = self.env["account.move"]
        self.TaxObj = self.env["account.tax"]

        self.JournalLedgerReportWizard = self.env["journal.ledger.report.wizard"]
        self.JournalLedgerReport = self.env[
            "report.account_financial_report.journal_ledger"
        ]
        self.company = self.env.ref("base.main_company")
        self.company.account_sale_tax_id = False
        self.company.account_purchase_tax_id = False

        today = datetime.today()
        last_year = today - relativedelta(years=1)

        self.previous_fy_date_start = Date.to_string(last_year.replace(month=1, day=1))
        self.previous_fy_date_end = Date.to_string(last_year.replace(month=12, day=31))
        self.fy_date_start = Date.to_string(today.replace(month=1, day=1))
        self.fy_date_end = Date.to_string(today.replace(month=12, day=31))

        self.receivable_account = self.AccountObj.search(
            [("user_type_id.name", "=", "Receivable")], limit=1
        )
        self.income_account = self.AccountObj.search(
            [("user_type_id.name", "=", "Income")], limit=1
        )
        self.expense_account = self.AccountObj.search(
            [("user_type_id.name", "=", "Expenses")], limit=1
        )
        self.payable_account = self.AccountObj.search(
            [("user_type_id.name", "=", "Payable")], limit=1
        )

        self.journal_sale = self.JournalObj.create(
            {
                "name": "Test journal sale",
                "code": "TST-JRNL-S",
                "type": "sale",
                "company_id": self.company.id,
            }
        )
        self.journal_purchase = self.JournalObj.create(
            {
                "name": "Test journal purchase",
                "code": "TST-JRNL-P",
                "type": "purchase",
                "company_id": self.company.id,
            }
        )

        self.tax_15_s = self.TaxObj.create(
            {
                "sequence": 30,
                "name": "Tax 15.0% (Percentage of Price)",
                "amount": 15.0,
                "amount_type": "percent",
                "include_base_amount": False,
                "type_tax_use": "sale",
            }
        )

        self.tax_20_s = self.TaxObj.create(
            {
                "sequence": 30,
                "name": "Tax 20.0% (Percentage of Price)",
                "amount": 20.0,
                "amount_type": "percent",
                "include_base_amount": False,
                "type_tax_use": "sale",
            }
        )

        self.tax_15_p = self.TaxObj.create(
            {
                "sequence": 30,
                "name": "Tax 15.0% (Percentage of Price)",
                "amount": 15.0,
                "amount_type": "percent",
                "include_base_amount": False,
                "type_tax_use": "purchase",
            }
        )

        self.tax_20_p = self.TaxObj.create(
            {
                "sequence": 30,
                "name": "Tax 20.0% (Percentage of Price)",
                "amount": 20.0,
                "amount_type": "percent",
                "include_base_amount": False,
                "type_tax_use": "purchase",
            }
        )

        self.partner_2 = self.env.ref("base.res_partner_2")

    def _add_move(
        self,
        date,
        journal,
        receivable_debit,
        receivable_credit,
        income_debit,
        income_credit,
    ):
        move_name = "move name"
        move_vals = {
            "journal_id": journal.id,
            "date": date,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": move_name,
                        "debit": receivable_debit,
                        "credit": receivable_credit,
                        "account_id": self.receivable_account.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": move_name,
                        "debit": income_debit,
                        "credit": income_credit,
                        "account_id": self.income_account.id,
                    },
                ),
            ],
        }
        return self.MoveObj.create(move_vals)

    def check_report_journal_debit_credit(
        self, res_data, expected_debit, expected_credit
    ):
        self.assertEqual(
            expected_debit, sum([rec["debit"] for rec in res_data["Journal_Ledgers"]])
        )

        self.assertEqual(
            expected_credit, sum([rec["credit"] for rec in res_data["Journal_Ledgers"]])
        )

    def check_report_journal_debit_credit_taxes(
        self,
        res_data,
        expected_base_debit,
        expected_base_credit,
        expected_tax_debit,
        expected_tax_credit,
    ):
        for rec in res_data["Journal_Ledgers"]:
            self.assertEqual(
                expected_base_debit,
                sum([tax_line["base_debit"] for tax_line in rec["tax_lines"]]),
            )
            self.assertEqual(
                expected_base_credit,
                sum([tax_line["base_credit"] for tax_line in rec["tax_lines"]]),
            )
            self.assertEqual(
                expected_tax_debit,
                sum([tax_line["tax_debit"] for tax_line in rec["tax_lines"]]),
            )
            self.assertEqual(
                expected_tax_credit,
                sum([tax_line["tax_credit"] for tax_line in rec["tax_lines"]]),
            )

    def test_01_test_total(self):
        today_date = Date.today()
        last_year_date = Date.to_string(datetime.today() - relativedelta(years=1))

        move1 = self._add_move(today_date, self.journal_sale, 0, 100, 100, 0)
        move2 = self._add_move(last_year_date, self.journal_sale, 0, 100, 100, 0)

        wiz = self.JournalLedgerReportWizard.create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "company_id": self.company.id,
                "journal_ids": [(6, 0, self.journal_sale.ids)],
                "move_target": "all",
            }
        )
        data = wiz._prepare_report_journal_ledger()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 100, 100)

        move3 = self._add_move(today_date, self.journal_sale, 0, 100, 100, 0)

        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 200, 200)
        wiz.move_target = "posted"
        data = wiz._prepare_report_journal_ledger()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 0, 0)

        move1.action_post()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 100, 100)

        move2.action_post()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 100, 100)

        move3.action_post()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 200, 200)

        wiz.date_from = self.previous_fy_date_start
        data = wiz._prepare_report_journal_ledger()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 300, 300)

    def test_02_test_taxes_out_invoice(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        move_form.partner_id = self.partner_2
        move_form.journal_id = self.journal_sale
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1.0
            line_form.price_unit = 100
            line_form.account_id = self.income_account
            line_form.tax_ids.add(self.tax_15_s)
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1.0
            line_form.price_unit = 100
            line_form.account_id = self.income_account
            line_form.tax_ids.add(self.tax_15_s)
            line_form.tax_ids.add(self.tax_20_s)
        invoice = move_form.save()
        invoice.action_post()

        wiz = self.JournalLedgerReportWizard.create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "company_id": self.company.id,
                "journal_ids": [(6, 0, self.journal_sale.ids)],
                "move_target": "all",
            }
        )
        data = wiz._prepare_report_journal_ledger()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)
        self.check_report_journal_debit_credit(res_data, 250, 250)
        self.check_report_journal_debit_credit_taxes(res_data, 0, 300, 0, 50)

    def test_03_test_taxes_in_invoice(self):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        move_form.partner_id = self.partner_2
        move_form.journal_id = self.journal_purchase
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1.0
            line_form.price_unit = 100
            line_form.account_id = self.expense_account
            line_form.tax_ids.add(self.tax_15_p)
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "test"
            line_form.quantity = 1.0
            line_form.price_unit = 100
            line_form.account_id = self.expense_account
            line_form.tax_ids.add(self.tax_15_p)
            line_form.tax_ids.add(self.tax_20_p)
        invoice = move_form.save()
        invoice.action_post()

        wiz = self.JournalLedgerReportWizard.create(
            {
                "date_from": self.fy_date_start,
                "date_to": self.fy_date_end,
                "company_id": self.company.id,
                "journal_ids": [(6, 0, self.journal_purchase.ids)],
                "move_target": "all",
            }
        )
        data = wiz._prepare_report_journal_ledger()
        res_data = self.JournalLedgerReport._get_report_values(wiz, data)

        self.check_report_journal_debit_credit(res_data, 250, 250)
        self.check_report_journal_debit_credit_taxes(res_data, 300, 0, 50, 0)
