import datetime

from odoo.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.income = cls.env["account.account"].create(
            [
                {"account_type": "income", "code": "INCOME", "name": "Income"},
            ]
        )
        cls.expense = cls.env["account.account"].create(
            [
                {"account_type": "expense", "code": "EXPENSE", "name": "Expense"},
            ]
        )
        cls.asset_cash = cls.env["account.account"].create(
            [
                {"account_type": "asset_cash", "code": "CASH", "name": "Cash"},
            ]
        )
        cls.journal = cls.env["account.journal"].create(
            {"code": "J", "name": "Journal", "type": "general"}
        )
        cls.move = cls.env["account.move"].create(
            {
                "journal_id": cls.journal.id,
                "date": datetime.date.today(),
                "line_ids": [
                    (0, 0, {"account_id": cls.income.id, "credit": 100}),
                    (0, 0, {"account_id": cls.expense.id, "debit": 80}),
                    (0, 0, {"account_id": cls.asset_cash.id, "debit": 20}),
                ],
            }
        )

    def test_account_move_line(self):
        balance_pl = sum([line.balance_pl for line in self.move.line_ids])
        self.assertEqual(balance_pl, 20)

        self.move.line_ids.account_id = self.asset_cash.id
        balance_pl = sum([line.balance_pl for line in self.move.line_ids])
        self.assertEqual(balance_pl, 0)
