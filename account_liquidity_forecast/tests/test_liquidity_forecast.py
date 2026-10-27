from datetime import date, timedelta
from io import BytesIO
from unittest.mock import patch

import xlsxwriter

from odoo import Command

from odoo.addons.account_liquidity_forecast.report.liquidity_forecast_xlsx import (
    copy_format,
)
from odoo.addons.base.tests.common import BaseCommon


class TestLiquidityForecastReport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env["report.account_liquidity_forecast.liquidity_forecast"]
        cls.company = cls.env.user.company_id
        cls.today = date.today()

        cls.base_data = {
            "company_id": cls.company.id,
            "date_from": (cls.today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "date_to": cls.today.strftime("%Y-%m-%d"),
            "period_length": "days",
            "only_posted_moves": True,
        }

    def _make_data(self, **overrides):
        """Return a copy of base_data with any field overridden."""
        return {**self.base_data, **overrides}

    def _get_or_create_general_journal(self):
        """Return the first general journal for the company, creating one if needed."""
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")],
            limit=1,
        )
        if not journal:
            journal = self.env["account.journal"].create(
                {
                    "name": "Test General Journal",
                    "code": "TGJ",
                    "type": "general",
                    "company_id": self.company.id,
                }
            )
        return journal

    def _create_account(self, code, name, account_type):
        """Convenience factory for account.account records."""
        return self.env["account.account"].create(
            {
                "code": code,
                "name": name,
                "account_type": account_type,
                "company_ids": [Command.link(self.company.id)],
            }
        )

    def _create_wizard(self, period_length="days", target_move="posted", date_to=None):
        """Convenience factory for the report wizard."""
        return self.env["account.liquidity.forecast.report.wizard"].create(
            {
                "company_id": self.company.id,
                "period_length": period_length,
                "date_to": date_to or self.today,
                "target_move": target_move,
            }
        )

    def test_generate_periods_days(self):
        """Daily periods: correct count and continuous sequences starting at 0."""
        data = self._make_data(
            date_from="2024-01-01",
            date_to="2024-01-05",
            period_length="days",
        )
        periods = self.report._generate_periods(data)

        self.assertEqual(len(periods), 5, "Should generate 5 daily periods")
        self.assertEqual(
            [p["sequence"] for p in periods],
            list(range(5)),
            "Sequences must be continuous from 0",
        )

    def test_generate_periods_months(self):
        """Monthly periods: correct count, boundaries, and 'Current' label on first."""
        data = self._make_data(
            date_from="2024-01-15",
            date_to="2024-03-10",
            period_length="months",
        )
        periods = self.report._generate_periods(data)

        self.assertEqual(len(periods), 3, "Should generate 3 monthly periods")
        self.assertIn(
            "Current", periods[0]["name"], "First period should contain 'Current'"
        )

        expected = [
            (date(2024, 1, 15), date(2024, 1, 31)),
            (date(2024, 2, 1), date(2024, 2, 29)),  # 2024 is a leap year
            (date(2024, 3, 1), date(2024, 3, 10)),
        ]
        for i, (exp_from, exp_to) in enumerate(expected):
            with self.subTest(period_index=i):
                self.assertEqual(periods[i]["date_from"], exp_from)
                self.assertEqual(periods[i]["date_to"], exp_to)

    def test_generate_periods_leap_year_february(self):
        """Monthly period covers all 29 days of February in a leap year."""
        data = self._make_data(
            date_from="2024-02-01",
            date_to="2024-02-29",
            period_length="months",
        )
        periods = self.report._generate_periods(data)

        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["date_from"], date(2024, 2, 1))
        self.assertEqual(periods[0]["date_to"], date(2024, 2, 29))

    def test_generate_periods_non_leap_year_february(self):
        """Monthly period covers all 28 days of February in a non-leap year."""
        data = self._make_data(
            date_from="2023-02-01",
            date_to="2023-02-28",
            period_length="months",
        )
        periods = self.report._generate_periods(data)

        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["date_from"], date(2023, 2, 1))
        self.assertEqual(periods[0]["date_to"], date(2023, 2, 28))

    def test_generate_periods_year_boundary(self):
        """Monthly periods spanning Dec→Jan land in the correct calendar years."""
        data = self._make_data(
            date_from="2023-12-15",
            date_to="2024-01-15",
            period_length="months",
        )
        periods = self.report._generate_periods(data)

        self.assertEqual(
            len(periods), 2, "Should produce 2 periods across the year boundary"
        )
        self.assertEqual(
            periods[0]["date_from"].year, 2023, "First period must be in 2023"
        )
        self.assertEqual(
            periods[1]["date_from"].year, 2024, "Second period must be in 2024"
        )

    def test_complete_beginning_balance_initial(self):
        """Beginning balance is initialised as a float for an empty period."""
        periods = self.report._generate_periods(self.base_data)
        period = periods[0]
        seq = period["sequence"]
        lines = [{"code": "beginning_balance", "periods": {seq: {}}}]

        self.report._complete_beginning_balance(self.base_data, lines, lines[0], period)

        amount = lines[0]["periods"][seq].get("amount")
        self.assertIsInstance(amount, float, "Beginning balance must be a float")

    def _run_net_cash_flow(self, in_amount, out_amount):
        """Helper: build lines, run _complete_net_cash_flow, return computed amount."""
        periods = self.report._generate_periods(self.base_data)
        period = periods[0]
        seq = period["sequence"]

        lines = [
            {
                "code": "cash_flow_line_in_account_101",
                "periods": {seq: {"amount": in_amount}},
            },
            {
                "code": "cash_flow_line_out_account_202",
                "periods": {seq: {"amount": out_amount}},
            },
            {"code": "net_cash_flow", "periods": {seq: {}}},
        ]
        self.report._complete_net_cash_flow(self.base_data, lines, lines[2], period)
        return lines[2]["periods"][seq].get("amount")

    def test_complete_net_cash_flow_positive(self):
        """Net cash flow correctly sums positive inflow and negative outflow."""
        self.assertEqual(self._run_net_cash_flow(200.0, -50.0), 150.0)

    def test_complete_net_cash_flow_zero_inflow(self):
        """Net cash flow handles zero inflow with a negative outflow."""
        self.assertEqual(self._run_net_cash_flow(0.0, -100.0), -100.0)

    def test_complete_net_cash_flow_both_zero(self):
        """Net cash flow is zero when both sides are zero."""
        self.assertEqual(self._run_net_cash_flow(0.0, 0.0), 0.0)

    def test_account_open_items_empty_cases(self):
        """Empty recordset or date=False returns an empty list."""
        Account = self.env["account.account"]
        self.assertEqual(Account._get_open_items_at_date(False, True), [])
        self.assertEqual(Account._get_open_items_at_date(self.today, True), [])

    def test_account_open_items_draft_vs_posted(self):
        """
        Draft lines are visible with only_posted_moves=False;
        invisible with only_posted_moves=True until the move is posted.
        """
        receivable = self._create_account(
            "TESTREC1", "Test Receivable", "asset_receivable"
        )
        journal = self._get_or_create_general_journal()

        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": self.today,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Debit line",
                            "account_id": receivable.id,
                            "debit": 100.0,
                            "credit": 0.0,
                            "date_maturity": self.today,
                            "partner_id": self.partner.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Credit line",
                            "account_id": receivable.id,
                            "debit": 0.0,
                            "credit": 100.0,
                            "date_maturity": self.today,
                            "partner_id": self.partner.id,
                        }
                    ),
                ],
            }
        )

        self.assertTrue(
            receivable._get_open_items_at_date(self.today, False),
            "Draft line should be visible when only_posted_moves=False",
        )
        self.assertFalse(
            receivable._get_open_items_at_date(self.today, True),
            "Draft line must NOT appear when only_posted_moves=True",
        )

        move.action_post()
        self.assertTrue(
            receivable._get_open_items_at_date(self.today, True),
            "Posted line must be visible when only_posted_moves=True",
        )

    def test_ir_actions_report_context_preparation(self):
        """_prepare_liquidity_forecast_report_context extracts lang and returns
        falsy for empty data."""
        report_model = self.env["ir.actions.report"]

        ctx = report_model._prepare_liquidity_forecast_report_context(
            {"liquidity_forecast_report_lang": "en_US"}
        )
        self.assertEqual(ctx.get("lang"), "en_US")

        ctx_empty = report_model._prepare_liquidity_forecast_report_context({})
        self.assertFalse(ctx_empty)

    def test_ir_actions_report_html_and_xlsx_rendering(self):
        """HTML and XLSX reports render successfully (both currency positions)."""
        report_model = self.env["ir.actions.report"]
        wizard = self._create_wizard(target_move="all")
        report_values = wizard._prepare_report_liquidity_forecast()

        html_report = report_model._render_qweb_html(
            "account_liquidity_forecast.liquidity_forecast",
            wizard.ids,
            data=report_values,
        )
        self.assertTrue(html_report, "HTML report must not be empty")

        for position in ("before", "after"):
            with self.subTest(currency_position=position):
                self.company.currency_id.position = position
                xlsx = report_model._render_xlsx(
                    "report_liquidity_forecast_xlsx", wizard.ids, data=report_values
                )
                self.assertTrue(
                    xlsx, f"XLSX report must not be empty (position={position})"
                )

    def test_ir_actions_report_xlsx_without_company_id(self):
        """XLSX rendering still works when company_id is absent from data."""
        report_model = self.env["ir.actions.report"]
        wizard = self._create_wizard(target_move="all")
        report_values = wizard._prepare_report_liquidity_forecast()

        def _mock_get_report_values(_self, docids, data_arg):
            return {
                "company_currency": self.company.currency_id,
                "currency_name": self.company.currency_id.name,
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "only_posted_moves": False,
                "periods": [{"sequence": 0, "name": "Period 1"}],
                "liquidity_forecast_lines": [
                    {
                        "title": "Line 1",
                        "level": "heading",
                        "periods": {0: {"amount": 100.0}},
                    }
                ],
            }

        report_cls = self.env[
            "report.account_liquidity_forecast.liquidity_forecast"
        ].__class__
        with patch.object(report_cls, "_get_report_values", _mock_get_report_values):
            data_no_company = {
                k: v for k, v in report_values.items() if k != "company_id"
            }
            xlsx = report_model._render_xlsx(
                "report_liquidity_forecast_xlsx", wizard.ids, data=data_no_company
            )
        self.assertTrue(xlsx, "XLSX must render even without company_id in data")

    def test_ir_actions_report_report_name(self):
        """_get_report_name returns a non-empty string with and without company_id."""
        xlsx_model = self.env["report.report_liquidity_forecast_xlsx"]
        self.assertTrue(
            xlsx_model._get_report_name(None, data={"company_id": self.company.id})
        )
        self.assertTrue(xlsx_model._get_report_name(None, data={}))

    def test_copy_format_helper(self):
        """copy_format returns a valid xlsxwriter Format object."""
        workbook = xlsxwriter.Workbook(BytesIO())
        fmt_original = workbook.add_format({"bold": True})
        fmt_copy = copy_format(workbook, fmt_original)
        self.assertTrue(fmt_copy, "copy_format must return a truthy Format object")

    def _setup_full_report_fixtures(self):
        """
        Create all accounting fixtures needed for the full report test:
        accounts, moves, bank journals, outstanding payments, and planning items.
        Returns (wizard, data_weeks) ready to use.
        """
        receivable = self._create_account(
            "TESTRECFL", "Test Rec Full", "asset_receivable"
        )
        payable = self._create_account(
            "TESTPAYFL", "Test Pay Full", "liability_payable"
        )
        journal = self._get_or_create_general_journal()

        # --- Open-items move (posted) ---
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": self.today,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Debit line",
                            "account_id": receivable.id,
                            "debit": 100.0,
                            "credit": 0.0,
                            "date_maturity": self.today,
                            "partner_id": self.partner.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Credit line",
                            "account_id": payable.id,
                            "debit": 0.0,
                            "credit": 100.0,
                            "date_maturity": self.today + timedelta(days=2),
                            "partner_id": self.partner.id,
                        }
                    ),
                ],
            }
        )
        move.action_post()

        payment_in_acc = self._create_account(
            "TESTBIN", "Test Bank Inbound", "asset_cash"
        )
        payment_out_acc = self._create_account(
            "TESTBOUT", "Test Bank Outbound", "asset_cash"
        )

        bank_journal = self.env["account.journal"].create(
            {
                "name": "Test Bank Journal LF",
                "code": "TBKLF",
                "type": "bank",
                "company_id": self.company.id,
            }
        )
        bank_journal.inbound_payment_method_line_ids.write(
            {"payment_account_id": payment_in_acc.id}
        )
        bank_journal.outbound_payment_method_line_ids.write(
            {"payment_account_id": payment_out_acc.id}
        )

        # Outstanding inbound payment move
        bank_move_in = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": bank_journal.id,
                "date": self.today,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Outstanding Payment In",
                            "account_id": payment_in_acc.id,
                            "debit": 150.0,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Outstanding Payment In Contra",
                            "account_id": receivable.id,
                            "debit": 0.0,
                            "credit": 150.0,
                        }
                    ),
                ],
            }
        )
        bank_move_in.action_post()

        # Outstanding outbound payment move
        bank_move_out = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": bank_journal.id,
                "date": self.today,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Outstanding Payment Out",
                            "account_id": payment_out_acc.id,
                            "debit": 0.0,
                            "credit": 50.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Outstanding Payment Out Contra",
                            "account_id": payable.id,
                            "debit": 50.0,
                            "credit": 0.0,
                        }
                    ),
                ],
            }
        )
        bank_move_out.action_post()

        planning_group = self.env["account.liquidity.forecast.planning.group"].create(
            {
                "name": "Test Planning Group LF",
                "company_id": self.company.id,
            }
        )
        PlanningItem = self.env["account.liquidity.forecast.planning.item"]
        PlanningItem.create(
            {
                "name": "Planned Item In (group) 1",
                "group_id": planning_group.id,
                "company_id": self.company.id,
                "amount": 250.0,
                "direction": "in",
                "date": self.today,
                "expiry_date": self.today + timedelta(days=10),
            }
        )
        PlanningItem.create(
            {
                "name": "Planned Item In (group) 2",
                "group_id": planning_group.id,
                "company_id": self.company.id,
                "amount": 50.0,
                "direction": "in",
                "date": self.today + timedelta(days=8),
                "expiry_date": self.today + timedelta(days=10),
            }
        )
        PlanningItem.create(
            {
                "name": "Planned Item Out (no group)",
                "group_id": False,
                "company_id": self.company.id,
                "amount": 100.0,
                "direction": "out",
                "date": self.today,
                "expiry_date": self.today + timedelta(days=10),
            }
        )

        wizard = self.env["account.liquidity.forecast.report.wizard"].create(
            {
                "company_id": self.company.id,
                "period_length": "weeks",
                "date_to": self.today + timedelta(days=20),
                "target_move": "all",
            }
        )
        data_weeks = self._make_data(
            wizard_id=wizard.id,
            date_from=(self.today - timedelta(days=10)).strftime("%Y-%m-%d"),
            date_to=(self.today + timedelta(days=20)).strftime("%Y-%m-%d"),
            period_length="weeks",
            only_posted_moves=False,
        )
        return wizard, data_weeks

    def test_liquidity_forecast_full_report(self):
        """
        End-to-end: prepare report lines from moves and planning items,
        verify report values are returned, and cover the payable cash-flow path.
        """
        wizard, data_weeks = self._setup_full_report_fixtures()

        # Weekly period generation must yield at least one period
        res_lines, periods = self.report._prepare_liquidity_forecast_lines(data_weeks)
        self.assertGreater(len(periods), 0, "Weekly periods must not be empty")
        self.assertGreater(len(res_lines), 0, "Report lines must not be empty")

        # _get_report_values round-trip
        report_values = self.report._get_report_values(wizard.ids, data_weeks)
        self.assertEqual(
            report_values["date_from"],
            data_weeks["date_from"],
            "_get_report_values must echo date_from back",
        )

        # Cover cash_flow_line_out_payable path via patch
        dummy_line = {"code": "cash_flow_line_out_payable", "periods": {}}
        dummy_period = {"sequence": 0}

        def _dummy_payable(*args, **kwargs):
            pass

        with patch.object(
            self.report.__class__,
            "_complete_cash_flow_lines_payable",
            _dummy_payable,
            create=True,
        ):
            self.report._complete_liquidity_forecast_lines(
                self.base_data, [dummy_line], dummy_line, dummy_period, [dummy_period]
            )

    def test_wizard_export_buttons(self):
        """All three export buttons execute without error and wizard prep is correct."""
        wizard = self._create_wizard(period_length="days", target_move="posted")

        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()

        res_prep = wizard._prepare_report_liquidity_forecast()
        self.assertTrue(
            res_prep["only_posted_moves"],
            "Wizard with target_move='posted' must set only_posted_moves=True",
        )
