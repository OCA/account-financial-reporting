# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAnalyticCashBasis(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.report_model = cls.env["analytic.cash.basis.line"]
        cls.plan = cls.env["account.analytic.plan"].create({"name": "Test Plan"})
        cls.boat_a = cls.env["account.analytic.account"].create(
            {"name": "Boat A", "plan_id": cls.plan.id}
        )
        cls.boat_b = cls.env["account.analytic.account"].create(
            {"name": "Boat B", "plan_id": cls.plan.id}
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _create_split_bill(self, amount, invoice_date, move_type="in_invoice"):
        """Bill (or invoice) of `amount` split 50/50 between the two accounts."""
        bill = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "date": invoice_date,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Docking service",
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": [(5, 0, 0)],
                            "analytic_distribution": {
                                str(self.boat_a.id): 50,
                                str(self.boat_b.id): 50,
                            },
                        },
                    )
                ],
            }
        )
        bill.action_post()
        return bill

    def _create_entry(self, journal, date, amount=300.0):
        """Miscellaneous entry with the whole amount on a single account."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": date,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Direct expense",
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                            "debit": amount,
                            "credit": 0.0,
                            "analytic_distribution": {str(self.boat_a.id): 100},
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Counterpart",
                            "account_id": self.company_data[
                                "default_account_payable"
                            ].id,
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _register_payment(self, bill, amount, payment_date):
        wizard = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=bill.ids)
            .create({"amount": amount, "payment_date": payment_date})
        )
        wizard._create_payments()

    def _rows(self, move, regime=None, analytic_account=None):
        self.env.flush_all()
        domain = [("move_id", "=", move.id)]
        if regime:
            domain.append(("regime", "=", regime))
        if analytic_account:
            domain.append(("analytic_account_id", "=", analytic_account.id))
        return self.report_model.search(domain)

    # ------------------------------------------------------------------
    # proration
    # ------------------------------------------------------------------
    def test_installments_are_prorated_per_analytic_account(self):
        """3,000 bill split 50/50, paid in 3x1,000 -> 500/month/account."""
        bill = self._create_split_bill(3000, "2026-03-10")
        for pay_date in ("2026-03-15", "2026-04-15", "2026-05-15"):
            self._register_payment(bill, 1000, fields.Date.to_date(pay_date))

        for boat in (self.boat_a, self.boat_b):
            accrual = self._rows(bill, "accrual", boat)
            self.assertEqual(len(accrual), 1)
            self.assertAlmostEqual(sum(accrual.mapped("amount")), -1500, places=2)
            self.assertEqual(accrual.date, fields.Date.to_date("2026-03-10"))
            self.assertEqual(accrual.bucket, "invoice")
            self.assertEqual(accrual.kind, "cost")

            cash = self._rows(bill, "cash", boat)
            self.assertEqual(len(cash), 3)
            self.assertEqual(
                [(r.date.isoformat(), round(r.amount, 2)) for r in cash.sorted("date")],
                [
                    ("2026-03-15", -500.0),
                    ("2026-04-15", -500.0),
                    ("2026-05-15", -500.0),
                ],
            )
            self.assertEqual(set(cash.mapped("bucket")), {"settlement"})

    def test_partial_payment_reports_only_the_settled_share(self):
        """Half paid: accrual keeps the full amount, cash shows only half."""
        bill = self._create_split_bill(1000, "2026-03-10")
        self._register_payment(bill, 500, fields.Date.to_date("2026-03-20"))

        accrual = self._rows(bill, "accrual", self.boat_a)
        cash = self._rows(bill, "cash", self.boat_a)
        self.assertAlmostEqual(sum(accrual.mapped("amount")), -500, places=2)
        self.assertAlmostEqual(sum(cash.mapped("amount")), -250, places=2)

    def test_unpaid_bill_has_no_cash_rows(self):
        bill = self._create_split_bill(1764.22, "2026-04-06")
        for boat in (self.boat_a, self.boat_b):
            self.assertTrue(self._rows(bill, "accrual", boat))
            self.assertFalse(self._rows(bill, "cash", boat))

    def test_customer_invoice_is_reported_as_revenue(self):
        invoice = self._create_split_bill(2000, "2026-05-05", move_type="out_invoice")
        self._register_payment(invoice, 2000, fields.Date.to_date("2026-05-20"))

        rows = self._rows(invoice, analytic_account=self.boat_a)
        self.assertEqual(set(rows.mapped("kind")), {"revenue"})
        cash = self._rows(invoice, "cash", self.boat_a)
        self.assertAlmostEqual(sum(cash.mapped("amount")), 1000, places=2)

    # ------------------------------------------------------------------
    # buckets
    # ------------------------------------------------------------------
    def test_direct_bank_expense_is_cash_on_its_own_date(self):
        """No invoice, no reconciliation: the entry date is the cash date."""
        move = self._create_entry(
            self.company_data["default_journal_bank"], "2026-06-10"
        )
        accrual = self._rows(move, "accrual", self.boat_a)
        cash = self._rows(move, "cash", self.boat_a)

        self.assertEqual(accrual.bucket, "direct")
        self.assertEqual(cash.bucket, "direct")
        self.assertEqual(cash.date, fields.Date.to_date("2026-06-10"))
        self.assertAlmostEqual(cash.amount, accrual.amount, places=2)

    def test_miscellaneous_entry_is_flagged_no_cash_event(self):
        """A misc entry never settles: accrual only, explicitly flagged."""
        move = self._create_entry(
            self.company_data["default_journal_misc"], "2026-06-11"
        )
        accrual = self._rows(move, "accrual", self.boat_a)
        self.assertEqual(accrual.bucket, "no_cash_event")
        self.assertFalse(self._rows(move, "cash", self.boat_a))

    # ------------------------------------------------------------------
    # exclusions
    # ------------------------------------------------------------------
    def test_manual_analytic_on_payable_line_is_excluded(self):
        """Analytic items on AP/AR accounts (the manual 'cash view' habit)
        must not reach the report in either regime."""
        bill = self._create_split_bill(1000, "2026-03-10")
        payable_line = bill.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        manual = self.env["account.analytic.line"].create(
            {
                "name": "manual duplicate",
                "account_id": self.boat_a.id,
                "amount": -1000,
                "date": "2026-03-12",
                "move_line_id": payable_line.id,
            }
        )
        self.env.flush_all()
        self.assertFalse(
            self.report_model.search([("analytic_line_id", "=", manual.id)])
        )

    def test_analytic_line_without_journal_item_is_excluded(self):
        """Timesheets carry no accounting amount to settle."""
        timesheet = self.env["account.analytic.line"].create(
            {
                "name": "8 hours",
                "account_id": self.boat_a.id,
                "amount": -800,
                "date": "2026-03-12",
            }
        )
        self.env.flush_all()
        self.assertFalse(
            self.report_model.search([("analytic_line_id", "=", timesheet.id)])
        )

    def test_draft_move_is_excluded(self):
        """Only posted moves reach the report."""
        bill = self._create_split_bill(500, "2026-03-10")
        bill.button_draft()
        self.env.flush_all()
        self.assertFalse(self._rows(bill))

    # ------------------------------------------------------------------
    # identity
    # ------------------------------------------------------------------
    def test_ids_are_deterministic_across_queries(self):
        """Group expansion and record rules re-read rows BY ID in a second
        query; ids must map to the same row every time (regression: ids came
        from row_number() OVER () and shuffled between executions)."""
        bill = self._create_split_bill(3000, "2026-03-10")
        for pay_date in ("2026-03-15", "2026-04-15"):
            self._register_payment(bill, 1000, fields.Date.to_date(pay_date))
        self.env.flush_all()

        rows = self.report_model.search([("move_id", "=", bill.id)])
        self.assertEqual(len(set(rows.ids)), len(rows))
        first_read = {
            row.id: (row.analytic_line_id.id, row.regime, row.amount) for row in rows
        }

        self.report_model.invalidate_model()
        second_read = {
            row.id: (row.analytic_line_id.id, row.regime, row.amount)
            for row in self.report_model.browse(sorted(first_read))
        }
        self.assertEqual(first_read, second_read)
