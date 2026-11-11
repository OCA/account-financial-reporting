# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import MagicMock, patch

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestBankReconciliationXlsx(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref("base.main_company")
        cls.bank_journal = cls.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )

        if not cls.bank_journal:
            cls.bank_journal = cls.env["account.journal"].create(
                {
                    "name": "Test Bank",
                    "code": "BNKT",
                    "type": "bank",
                    "company_id": cls.company.id,
                }
            )

        cls.report_model = cls.env["report.bank.reconciliation.xlsx"]
        cls.wizard_model = cls.env["bank.reconciliation.report.wizard"]
        cls.today = fields.Date.context_today(cls.env.user)

    def test_compute_account_balance_empty(self):
        with patch.object(self.env.cr, "dictfetchall", return_value=[]):
            balance = self.report_model._compute_account_balance(
                self.bank_journal, self.today
            )
            self.assertEqual(balance, 0.0)

    def test_compute_account_balance_none_sum(self):
        with patch.object(self.env.cr, "dictfetchall", return_value=[{"sum": None}]):
            balance = self.report_model._compute_account_balance(
                self.bank_journal, self.today
            )
            self.assertEqual(balance, 0.0)

    def test_compute_account_balance_with_value(self):
        with patch.object(self.env.cr, "dictfetchall", return_value=[{"sum": 150.50}]):
            balance = self.report_model._compute_account_balance(
                self.bank_journal, self.today
            )
            self.assertEqual(balance, 150.50)

    def test_prepare_move_lines_empty(self):
        move_lines = self.report_model._prepare_move_lines(
            self.bank_journal, self.today
        )
        self.assertIsInstance(move_lines, list)

    def test_prepare_move_lines_structure(self):
        move_lines = self.report_model._prepare_move_lines(
            self.bank_journal, self.today
        )
        if move_lines:
            line = move_lines[0]
            required = {
                "date",
                "label",
                "ref",
                "partner",
                "amount",
                "statement_line_date",
                "move_number",
                "counterpart",
            }
            self.assertTrue(required.issubset(line.keys()))

    def test_prepare_draft_statement_lines_empty(self):
        draft_lines = self.report_model._prepare_draft_statement_lines(
            self.bank_journal, self.today
        )
        self.assertIsInstance(draft_lines, list)

    def test_prepare_draft_statement_lines_structure(self):
        draft_lines = self.report_model._prepare_draft_statement_lines(
            self.bank_journal, self.today
        )
        if draft_lines:
            line = draft_lines[0]
            required = {"date", "label", "ref", "partner", "amount", "statement_ref"}
            self.assertTrue(required.issubset(line.keys()))

    def test_wizard_creation(self):
        wizard = self.wizard_model.create({"date": self.today})
        self.assertTrue(wizard.exists())
        self.assertEqual(wizard.date, self.today)

    def test_wizard_default_journal_ids(self):
        wizard = self.wizard_model.create({"date": self.today})
        default_journals = wizard._default_journal_ids()
        self.assertIsInstance(default_journals, type(self.env["account.journal"]))

    def test_wizard_xlsx_action(self):
        wizard = self.wizard_model.create(
            {
                "date": self.today,
                "journal_ids": [Command.set([self.bank_journal.id])],
            }
        )
        action = wizard.open_xlsx()
        self.assertIsInstance(action, dict)
        self.assertIn("type", action)

    def test_generate_xlsx_report_with_journals(self):
        wizard = self.wizard_model.create(
            {
                "date": self.today,
                "journal_ids": [Command.set([self.bank_journal.id])],
            }
        )
        workbook = MagicMock()
        workbook.add_worksheet.return_value = MagicMock()
        workbook.add_format.return_value = MagicMock()
        self.report_model.generate_xlsx_report(workbook, {}, wizard)
        workbook.add_worksheet.assert_called()

    def test_generate_xlsx_report_no_journals(self):
        wizard = self.wizard_model.create(
            {
                "date": self.today,
                "journal_ids": [Command.set([])],
            }
        )
        workbook = MagicMock()
        workbook.add_worksheet.return_value = MagicMock()
        workbook.add_format.return_value = MagicMock()
        self.report_model.generate_xlsx_report(workbook, {}, wizard)
        workbook.add_worksheet.assert_called()

    @patch(
        "odoo.addons.account_bank_reconciliation_summary_xlsx.report."
        "bank_reconciliation_xlsx.BankReconciliationXlsx._prepare_move_lines"
    )
    def test_generate_xlsx_report_with_move_lines(self, mock_move_lines):
        mock_move_lines.return_value = [
            {
                "date": self.today,
                "label": "Test Move",
                "ref": "REF001",
                "partner": "Test Partner",
                "amount": 100.0,
                "statement_line_date": "",
                "move_number": "MOVE001",
                "counterpart": "ACC001",
            }
        ]
        wizard = self.wizard_model.create(
            {
                "date": self.today,
                "journal_ids": [Command.set([self.bank_journal.id])],
            }
        )
        workbook = MagicMock()
        workbook.add_worksheet.return_value = MagicMock()
        workbook.add_format.return_value = MagicMock()
        self.report_model.generate_xlsx_report(workbook, {}, wizard)
        mock_move_lines.assert_called()

    @patch(
        "odoo.addons.account_bank_reconciliation_summary_xlsx.report."
        "bank_reconciliation_xlsx.BankReconciliationXlsx._prepare_draft_statement_lines"
    )
    def test_generate_xlsx_report_with_statement_lines(self, mock_statement_lines):
        mock_statement_lines.return_value = [
            {
                "date": self.today,
                "label": "Test Statement Line",
                "ref": "REF002",
                "partner": "Test Partner",
                "amount": 50.0,
                "statement_ref": "STMT001",
            }
        ]
        wizard = self.wizard_model.create(
            {
                "date": self.today,
                "journal_ids": [Command.set([self.bank_journal.id])],
            }
        )
        workbook = MagicMock()
        workbook.add_worksheet.return_value = MagicMock()
        workbook.add_format.return_value = MagicMock()
        self.report_model.generate_xlsx_report(workbook, {}, wizard)
        mock_statement_lines.assert_called()

    def test_language_handling_no_lang(self):
        original_lang = self.env.user.lang
        self.env.user.lang = False
        try:
            wizard = self.wizard_model.create(
                {
                    "date": self.today,
                    "journal_ids": [Command.set([self.bank_journal.id])],
                }
            )
            workbook = MagicMock()
            workbook.add_worksheet.return_value = MagicMock()
            workbook.add_format.return_value = MagicMock()
            self.report_model.generate_xlsx_report(workbook, {}, wizard)
        finally:
            self.env.user.lang = original_lang
