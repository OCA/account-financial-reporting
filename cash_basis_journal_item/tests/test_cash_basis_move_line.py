# Copyright 2026 PT Solusi Aglis Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.fields import Date
from odoo.tests.common import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestCashBasisMoveLine(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.currency = cls.company.currency_id
        cls.CashBasisLine = cls.env["cash.basis.move.line"]

        # Accounts
        cls.account_receivable = cls.env["account.account"].create(
            {
                "code": "CBREC",
                "name": "CB Test Receivable",
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.account_revenue = cls.env["account.account"].create(
            {
                "code": "CBREV",
                "name": "CB Test Revenue",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "company_id": cls.company.id,
            }
        )
        cls.account_payable = cls.env["account.account"].create(
            {
                "code": "CBPAY",
                "name": "CB Test Payable",
                "user_type_id": cls.env.ref("account.data_account_type_payable").id,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.account_expense = cls.env["account.account"].create(
            {
                "code": "CBEXP",
                "name": "CB Test Expense",
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
                "company_id": cls.company.id,
            }
        )
        # Journals
        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "CB Test Sale",
                "code": "CBSL",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )
        cls.purchase_journal = cls.env["account.journal"].create(
            {
                "name": "CB Test Purchase",
                "code": "CBPU",
                "type": "purchase",
                "company_id": cls.company.id,
            }
        )
        cls.bank_journal = cls.env["account.journal"].create(
            {
                "name": "CB Test Bank",
                "code": "CBBK",
                "type": "bank",
                "company_id": cls.company.id,
            }
        )
        cls.account_bank = cls.bank_journal.default_account_id
        cls.general_journal = cls.env["account.journal"].create(
            {
                "name": "CB Test General",
                "code": "CBGN",
                "type": "general",
                "company_id": cls.company.id,
            }
        )

        # Partner
        cls.partner = cls.env["res.partner"].create({"name": "CB Test Partner"})

    def _create_invoice(self, move_type="out_invoice", amount=1000.0):
        """Helper to create and post an invoice."""
        if move_type in ("out_invoice", "out_refund"):
            journal = self.sale_journal
            line_account = self.account_revenue
        else:
            journal = self.purchase_journal
            line_account = self.account_expense
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "journal_id": journal.id,
                "invoice_date": Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "account_id": line_account.id,
                            "quantity": 1,
                            "price_unit": amount,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _create_payment(self, amount=1000.0, payable_account=None):
        """Helper to create and post a bank payment entry."""
        account = payable_account or self.account_payable
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 0,
                            "credit": amount,
                            "partner_id": self.partner.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": account.id,
                            "debit": amount,
                            "credit": 0,
                            "partner_id": self.partner.id,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _create_customer_payment(self, amount=1000.0, receivable_account=None):
        """Helper to create a customer bank receipt entry."""
        account = receivable_account or self.account_receivable
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": amount,
                            "credit": 0,
                            "partner_id": self.partner.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": account.id,
                            "debit": 0,
                            "credit": amount,
                            "partner_id": self.partner.id,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def test_01_direct_copy_bank_journal(self):
        """Test direct copy from bank journal entries."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 500.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 0,
                            "credit": 500.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()

        # Run the cron
        self.CashBasisLine._cron_generate_cash_basis_lines()

        # Check cash basis lines were created
        cb_lines = self.CashBasisLine.search(
            [("move_id", "=", move.id), ("partial_reconcile_id", "=", False)]
        )
        self.assertTrue(
            cb_lines, "Direct copy lines should be created for bank journal"
        )
        self.assertEqual(len(cb_lines), 2, "Should have 2 lines (debit + credit)")

        # Check amounts are 100%
        debit_line = cb_lines.filtered(lambda r: r.debit > 0)
        credit_line = cb_lines.filtered(lambda r: r.credit > 0)
        self.assertAlmostEqual(debit_line.debit, 500.0)
        self.assertAlmostEqual(credit_line.credit, 500.0)

    def test_02_direct_copy_general_journal(self):
        """Test direct copy from general journal entries."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.general_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_expense.id,
                            "debit": 200.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 0,
                            "credit": 200.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search([("move_id", "=", move.id)])
        self.assertEqual(len(cb_lines), 2)
        self.assertAlmostEqual(sum(cb_lines.mapped("debit")), 200.0)
        self.assertAlmostEqual(sum(cb_lines.mapped("credit")), 200.0)

    def test_03_no_direct_copy_for_sale_journal(self):
        """Sale journal entries should NOT be directly copied."""
        invoice = self._create_invoice("out_invoice", 1000.0)

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search(
            [("move_id", "=", invoice.id), ("partial_reconcile_id", "=", False)]
        )
        self.assertFalse(cb_lines, "Sale journal entries should not be directly copied")

    def test_04_no_duplicate_on_rerun(self):
        """Running the cron twice should not duplicate lines."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 300.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 0,
                            "credit": 300.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()

        # Run cron twice
        self.CashBasisLine._cron_generate_cash_basis_lines()
        count_after_first = self.CashBasisLine.search_count([("move_id", "=", move.id)])
        self.CashBasisLine._cron_generate_cash_basis_lines()
        count_after_second = self.CashBasisLine.search_count(
            [("move_id", "=", move.id)]
        )
        self.assertEqual(
            count_after_first,
            count_after_second,
            "Rerunning cron should not create duplicate lines",
        )

    def test_05_full_reconciliation_customer_invoice(self):
        """Test proportional recognition on full payment of customer invoice."""
        invoice = self._create_invoice("out_invoice", 1000.0)
        # Get the receivable account used by the invoice
        inv_receivable = invoice.line_ids.filtered(
            lambda r: r.account_id.internal_type == "receivable"
        ).account_id
        payment = self._create_customer_payment(
            1000.0, receivable_account=inv_receivable
        )

        # Reconcile receivable lines
        receivable_lines = (
            (invoice + payment)
            .mapped("line_ids")
            .filtered(lambda r: r.account_id.internal_type == "receivable")
        )
        receivable_lines.reconcile()

        # Run the cron
        self.CashBasisLine._cron_generate_cash_basis_lines()

        # Check reconciliation lines were created for the invoice
        cb_lines = self.CashBasisLine.search(
            [
                ("move_id", "=", invoice.id),
                ("partial_reconcile_id", "!=", False),
            ]
        )
        self.assertTrue(
            cb_lines,
            "Reconciliation lines should be created for the invoice",
        )
        # Full payment: total debit should equal total credit
        total_debit = sum(cb_lines.mapped("debit"))
        total_credit = sum(cb_lines.mapped("credit"))
        self.assertAlmostEqual(
            total_debit,
            total_credit,
            places=2,
            msg="Total debit must equal total credit",
        )

    def test_06_partial_reconciliation(self):
        """Test proportional recognition on partial payment."""
        invoice = self._create_invoice("out_invoice", 1000.0)
        inv_receivable = invoice.line_ids.filtered(
            lambda r: r.account_id.internal_type == "receivable"
        ).account_id
        # Pay only 400 out of 1000
        payment = self._create_customer_payment(
            400.0, receivable_account=inv_receivable
        )

        receivable_lines = (
            (invoice + payment)
            .mapped("line_ids")
            .filtered(lambda r: r.account_id.internal_type == "receivable")
        )
        receivable_lines.reconcile()

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search(
            [
                ("move_id", "=", invoice.id),
                ("partial_reconcile_id", "!=", False),
            ]
        )
        self.assertTrue(cb_lines, "Partial reconciliation lines should be created")
        # Percentage should be ~40%
        for line in cb_lines:
            self.assertAlmostEqual(line.reconcile_percentage, 40.0, places=1)

    def test_07_vendor_bill_payment(self):
        """Test cash basis for vendor bill with payment."""
        bill = self._create_invoice("in_invoice", 500.0)
        bill_payable = bill.line_ids.filtered(
            lambda r: r.account_id.internal_type == "payable"
        ).account_id
        payment = self._create_payment(500.0, payable_account=bill_payable)

        payable_lines = (
            (bill + payment)
            .mapped("line_ids")
            .filtered(lambda r: r.account_id.internal_type == "payable")
        )
        payable_lines.reconcile()

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search(
            [
                ("move_id", "=", bill.id),
                ("partial_reconcile_id", "!=", False),
            ]
        )
        self.assertTrue(cb_lines, "Vendor bill reconciliation lines should exist")
        total_debit = sum(cb_lines.mapped("debit"))
        total_credit = sum(cb_lines.mapped("credit"))
        self.assertAlmostEqual(total_debit, total_credit, places=2)

    def test_08_cash_basis_line_fields(self):
        """Test that cash basis line fields are properly populated."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "ref": "TEST-REF-001",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Bank debit",
                            "account_id": self.account_bank.id,
                            "debit": 750.0,
                            "credit": 0,
                            "partner_id": self.partner.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Revenue credit",
                            "account_id": self.account_revenue.id,
                            "debit": 0,
                            "credit": 750.0,
                            "partner_id": self.partner.id,
                        },
                    ),
                ],
            }
        )
        move.action_post()

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search([("move_id", "=", move.id)])
        self.assertEqual(len(cb_lines), 2)

        for cb_line in cb_lines:
            self.assertEqual(cb_line.move_id, move)
            self.assertTrue(cb_line.move_line_id)
            self.assertEqual(cb_line.date, Date.today())
            self.assertEqual(cb_line.partner_id, self.partner)
            self.assertEqual(cb_line.journal_id, self.bank_journal)
            self.assertEqual(cb_line.company_id, self.company)
            self.assertEqual(cb_line.ref, "TEST-REF-001")
            self.assertAlmostEqual(cb_line.reconcile_percentage, 100.0)

    def test_09_balance_field(self):
        """Test that balance = debit - credit."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 100.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search([("move_id", "=", move.id)])
        for cb_line in cb_lines:
            self.assertAlmostEqual(
                cb_line.balance,
                cb_line.debit - cb_line.credit,
                places=2,
            )

    def test_10_draft_move_ignored(self):
        """Draft (unposted) moves should not be processed."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 100.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_revenue.id,
                            "debit": 0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        # Do NOT post the move

        self.CashBasisLine._cron_generate_cash_basis_lines()

        cb_lines = self.CashBasisLine.search([("move_id", "=", move.id)])
        self.assertFalse(cb_lines, "Draft moves should not generate cash basis lines")

    def test_11_both_cash_journals_skip_reconciliation(self):
        """When both sides of reconciliation are cash journals, skip Source 2."""
        # Create two bank journal entries and reconcile them
        move1 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 100.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_receivable.id,
                            "debit": 0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        move2 = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.bank_journal.id,
                "date": Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_receivable.id,
                            "debit": 100.0,
                            "credit": 0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account_bank.id,
                            "debit": 0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        move1.action_post()
        move2.action_post()

        receivable_lines = (
            (move1 + move2)
            .mapped("line_ids")
            .filtered(lambda r: r.account_id == self.account_receivable)
        )
        receivable_lines.reconcile()

        self.CashBasisLine._cron_generate_cash_basis_lines()

        # Direct copy lines should exist (Source 1)
        direct_lines = self.CashBasisLine.search(
            [
                ("move_id", "in", (move1 | move2).ids),
                ("partial_reconcile_id", "=", False),
            ]
        )
        self.assertTrue(direct_lines, "Direct copy lines should exist")

        # Reconciliation lines should NOT exist (both are cash journals)
        recon_lines = self.CashBasisLine.search(
            [
                ("move_id", "in", (move1 | move2).ids),
                ("partial_reconcile_id", "!=", False),
            ]
        )
        self.assertFalse(
            recon_lines,
            "Both-cash-journal reconciliation should not create Source 2 lines",
        )
