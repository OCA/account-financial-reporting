# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveLineCumulatedBalance(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.company_data["default_account_assets"]
        cls.counterpart_account = cls.company_data["default_account_revenue"]

    def _create_move(self, date, balance, partner=None):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.to_date(date),
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account.id,
                            "balance": balance,
                            "partner_id": partner.id if partner else False,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self.counterpart_account.id,
                            "balance": -balance,
                            "partner_id": partner.id if partner else False,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def test_cumulated_balance_includes_initial_balance(self):
        self._create_move("2023-12-31", 100)
        self._create_move("2024-01-15", 50)
        self._create_move("2024-02-15", -20)

        results = (
            self.env["account.move.line"]
            .with_context(account_move_line_cumulated_balance_guard=True)
            .search_read(
                domain=[
                    ("display_type", "not in", ["line_section", "line_note"]),
                    ("account_id", "=", self.account.id),
                    ("date", ">=", "2024-01-01"),
                    ("date", "<=", "2024-12-31"),
                    ("parent_state", "=", "posted"),
                ],
                fields=["balance", "cumulated_balance"],
                order="date desc, id desc",
            )
        )

        self.assertEqual(
            [(result["balance"], result["cumulated_balance"]) for result in results],
            [(-20, 130), (50, 150)],
        )

    def test_cumulated_balance_includes_initial_balance_with_ascending_date(self):
        self._create_move("2023-12-31", 100)
        self._create_move("2024-01-15", 50)
        self._create_move("2024-02-15", -20)

        results = (
            self.env["account.move.line"]
            .with_context(account_move_line_cumulated_balance_guard=True)
            .search_read(
                domain=[
                    ("display_type", "not in", ["line_section", "line_note"]),
                    ("account_id", "=", self.account.id),
                    ("date", ">=", "2024-01-01"),
                    ("date", "<=", "2024-12-31"),
                    ("parent_state", "=", "posted"),
                ],
                fields=["balance", "cumulated_balance"],
                order="date asc, id asc",
            )
        )

        self.assertEqual(
            [(result["balance"], result["cumulated_balance"]) for result in results],
            [(50, 150), (-20, 130)],
        )

    def test_cumulated_balance_with_several_year_filters(self):
        self._create_move("2024-12-31", 100)
        self._create_move("2025-01-15", 50)
        self._create_move("2026-01-15", 20)

        results = (
            self.env["account.move.line"]
            .with_context(account_move_line_cumulated_balance_guard=True)
            .search_read(
                domain=[
                    ("account_id", "=", self.account.id),
                    "|",
                    "&",
                    ("date", ">=", "2026-01-01"),
                    ("date", "<=", "2026-12-31"),
                    "&",
                    ("date", ">=", "2025-01-01"),
                    ("date", "<=", "2025-12-31"),
                    ("parent_state", "=", "posted"),
                ],
                fields=["date", "balance", "cumulated_balance"],
                order="date desc, id desc",
            )
        )

        self.assertEqual(
            [
                (result["date"], result["balance"], result["cumulated_balance"])
                for result in results
            ],
            [
                (fields.Date.to_date("2026-01-15"), 20, 170),
                (fields.Date.to_date("2025-01-15"), 50, 150),
            ],
        )

    def test_cumulated_balance_read_group_uses_first_line(self):
        self._create_move("2023-12-31", 100)
        self._create_move("2024-01-15", 50)
        self._create_move("2024-02-15", -20)

        groups = (
            self.env["account.move.line"]
            .with_context(account_move_line_cumulated_balance_guard=True)
            .read_group(
                domain=[
                    ("display_type", "not in", ["line_section", "line_note"]),
                    ("account_id", "=", self.account.id),
                    ("date", ">=", "2024-01-01"),
                    ("date", "<=", "2024-12-31"),
                    ("parent_state", "=", "posted"),
                ],
                fields=["cumulated_balance:max"],
                groupby=["account_id"],
            )
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["cumulated_balance"], 130)

    def test_cumulated_balance_respects_partner_groupby(self):
        partner_a = self.env["res.partner"].create({"name": "Partner A"})
        partner_b = self.env["res.partner"].create({"name": "Partner B"})
        self._create_move("2023-12-31", 100, partner_a)
        self._create_move("2023-12-31", 200, partner_b)
        self._create_move("2024-01-15", 50, partner_a)
        self._create_move("2024-01-15", 70, partner_b)

        results = (
            self.env["account.move.line"]
            .with_context(
                account_move_line_cumulated_balance_guard=True,
                group_by=["account_id", "partner_id"],
            )
            .search_read(
                domain=[
                    ("account_id", "=", self.account.id),
                    ("date", ">=", "2024-01-01"),
                    ("date", "<=", "2024-12-31"),
                    ("parent_state", "=", "posted"),
                ],
                fields=["partner_id", "balance", "cumulated_balance"],
                order="date desc, id desc",
            )
        )

        self.assertEqual(
            {
                result["partner_id"][0]: (
                    result["balance"],
                    result["cumulated_balance"],
                )
                for result in results
            },
            {
                partner_a.id: (50, 150),
                partner_b.id: (70, 270),
            },
        )

    def test_cumulated_balance_without_partner_groupby_accumulates_all_partners(self):
        partner_a = self.env["res.partner"].create({"name": "Partner A"})
        partner_b = self.env["res.partner"].create({"name": "Partner B"})
        self._create_move("2023-12-31", 100, partner_a)
        self._create_move("2023-12-31", 200, partner_b)
        self._create_move("2024-01-15", 50, partner_a)
        self._create_move("2024-01-15", 70, partner_b)

        results = (
            self.env["account.move.line"]
            .with_context(account_move_line_cumulated_balance_guard=True)
            .search_read(
                domain=[
                    ("account_id", "=", self.account.id),
                    ("date", ">=", "2024-01-01"),
                    ("date", "<=", "2024-12-31"),
                    ("parent_state", "=", "posted"),
                ],
                fields=["partner_id", "balance", "cumulated_balance"],
                order="date desc, id desc",
            )
        )

        self.assertEqual(
            [
                (
                    result["partner_id"][0],
                    result["balance"],
                    result["cumulated_balance"],
                )
                for result in results
            ],
            [
                (partner_b.id, 70, 420),
                (partner_a.id, 50, 350),
            ],
        )
