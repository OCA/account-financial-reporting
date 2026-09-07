# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestCashFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "TEST"})
        cls.report = cls.env.ref("mis_builder_cash_flow.mis_instance_cash_flow")
        cls.report.company_id = cls.company
        cls.bank_account = cls.env["account.account"].create(
            {
                "company_ids": [Command.set(cls.company.ids)],
                "code": "TEST1",
                "name": "Bank account 01",
                "account_type": "asset_cash",
            }
        )
        cls.bank_account_hide = cls.env["account.account"].create(
            {
                "company_ids": [Command.set(cls.company.ids)],
                "code": "TEST2",
                "name": "Bank account 02",
                "account_type": "asset_cash",
                "hide_in_cash_flow": True,
            }
        )
        cls.account = cls.env["account.account"].create(
            {
                "company_ids": [Command.set(cls.company.ids)],
                "code": "TEST3",
                "name": "Account",
                "account_type": "asset_cash",
                "reconcile": True,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Journal",
                "code": "JOURNAL",
                "company_id": cls.company.id,
                "type": "general",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        cls.plan_monthly = cls.env["mis.cash.flow.plan"].create(
            {
                "name": "Plan Monthly",
                "account_id": cls.account.id,
                "balance": 100,
                "company_id": cls.company.id,
                "date_start": Date.to_date("2024-01-01"),
                "date_end": Date.to_date("2024-03-01"),
                "periodicity": "months",
            }
        )
        cls.plan_weekly = cls.env["mis.cash.flow.plan"].create(
            {
                "name": "Plan Weekly",
                "account_id": cls.account.id,
                "balance": 100,
                "company_id": cls.company.id,
                "date_start": Date.to_date("2024-01-01"),
                "date_end": Date.to_date("2024-01-22"),
                "periodicity": "weeks",
            }
        )
        cls.plan_days = cls.env["mis.cash.flow.plan"].create(
            {
                "name": "Plan Days",
                "account_id": cls.account.id,
                "balance": 100,
                "company_id": cls.company.id,
                "date_start": Date.to_date("2024-01-01"),
                "date_end": Date.to_date("2024-01-21"),
                "periodicity": "days",
                "every_x_days": 10,
            }
        )
        cls.plan_with_values = cls.env["mis.cash.flow.plan"].create(
            {
                "name": "My Plan",
                "account_id": cls.account.id,
                "balance": 100,
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "date_start": Date.to_date("2024-01-01"),
                "date_end": Date.to_date("2024-01-01"),
                "periodicity": "months",
            }
        )
        cls.plan_regenerate = cls.env["mis.cash.flow.plan"].create(
            {
                "name": "Plan Regenerate",
                "account_id": cls.account.id,
                "balance": 100,
                "company_id": cls.company.id,
                "date_start": Date.to_date("2024-01-01"),
                "date_end": Date.to_date("2024-02-01"),
                "periodicity": "months",
            }
        )
        cls.plan_limit = cls.env["mis.cash.flow.plan"].create(
            {
                "name": "Plan Limit",
                "account_id": cls.account.id,
                "balance": 100,
                "company_id": cls.company.id,
                "date_start": Date.to_date("2024-01-01"),
                "date_end": Date.to_date("2024-12-31"),
                "periodicity": "days",
                "every_x_days": 1,
            }
        )

    def test_company_constrain(self):
        # Create another company
        other_company = self.env["res.company"].create({"name": "OTHER_COMPANY"})
        # Try to create a forecast line with a company that is not in the
        # account's companies
        with self.assertRaises(ValidationError):
            self.env["mis.cash_flow.forecast_line"].create(
                {
                    "account_id": self.account.id,  # Account belongs to self.company
                    "date": Date.today(),
                    "balance": 1000,
                    "company_id": other_company.id,  # Different company
                }
            )
        # Test that it works when the company is in the account's companies
        forecast_line = self.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": self.account.id,  # Account belongs to self.company
                "date": Date.today(),
                "balance": 1000,
                "company_id": self.company.id,  # Same company
            }
        )
        self.assertTrue(forecast_line.id)  # Should be created successfully

    def test_report_instance(self):
        self.check_matrix()
        move = self.env["account.move"].create(
            {
                "name": "Move",
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "move_type": "entry",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.bank_account.id,
                            "debit": 1500,
                            "credit": 0,
                            "company_id": self.company.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.bank_account_hide.id,
                            "debit": 500,
                            "credit": 0,
                            "company_id": self.company.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account.id,
                            "debit": 0,
                            "credit": 2000,
                            "company_id": self.company.id,
                        },
                    ),
                ],
            }
        )
        move._post()
        self.check_matrix(
            args=[
                ("liquidity", "Current", 1500),
                ("balance", "Current", 1500),
                ("in_receivable", "Current", -2000),
            ],
            ignore_rows=["balance", "period_balance", "in_total"],
        )
        date = Date.today() + timedelta(weeks=8)
        self.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": self.account.id,
                "date": date,
                "balance": 1000,
                "company_id": self.company.id,
            }
        )
        self.check_matrix(
            [
                ("liquidity", "Current", 1500),
                ("balance", "Current", 1500),
                ("in_receivable", "Current", -2000),
                ("in_forecast", "+8w", 1000),
            ],
            ignore_rows=["balance", "period_balance", "in_total"],
        )

    def test_plan_date_constrain(self):
        with self.assertRaises(ValidationError):
            self.env["mis.cash.flow.plan"].create(
                {
                    "name": "Invalid Plan",
                    "account_id": self.account.id,
                    "balance": 100,
                    "company_id": self.company.id,
                    "date_start": Date.to_date("2024-03-01"),
                    "date_end": Date.to_date("2024-01-01"),
                    "periodicity": "months",
                }
            )

    def test_plan_every_x_days_constrain(self):
        with self.assertRaises(ValidationError):
            self.env["mis.cash.flow.plan"].create(
                {
                    "name": "Invalid Plan",
                    "account_id": self.account.id,
                    "balance": 100,
                    "company_id": self.company.id,
                    "date_start": Date.to_date("2024-01-01"),
                    "date_end": Date.to_date("2024-03-01"),
                    "periodicity": "days",
                    "every_x_days": 0,
                }
            )

    def test_plan_generate_forecasts_monthly(self):
        self.plan_monthly.action_generate_forecast_lines()
        self.assertEqual(len(self.plan_monthly.forecast_line_ids), 3)
        self.assertEqual(
            sorted(self.plan_monthly.forecast_line_ids.mapped("date")),
            [
                Date.to_date("2024-01-01"),
                Date.to_date("2024-02-01"),
                Date.to_date("2024-03-01"),
            ],
        )

    def test_plan_generate_forecasts_weekly(self):
        self.plan_weekly.action_generate_forecast_lines()
        self.assertEqual(len(self.plan_weekly.forecast_line_ids), 4)
        self.assertEqual(
            sorted(self.plan_weekly.forecast_line_ids.mapped("date")),
            [
                Date.to_date("2024-01-01"),
                Date.to_date("2024-01-08"),
                Date.to_date("2024-01-15"),
                Date.to_date("2024-01-22"),
            ],
        )

    def test_plan_generate_forecasts_days(self):
        self.plan_days.action_generate_forecast_lines()
        self.assertEqual(len(self.plan_days.forecast_line_ids), 3)
        self.assertEqual(
            sorted(self.plan_days.forecast_line_ids.mapped("date")),
            [
                Date.to_date("2024-01-01"),
                Date.to_date("2024-01-11"),
                Date.to_date("2024-01-21"),
            ],
        )

    def test_plan_regenerate_removes_previous_lines(self):
        self.plan_regenerate.action_generate_forecast_lines()
        first_line_ids = self.plan_regenerate.forecast_line_ids.ids
        self.plan_regenerate.date_end = Date.to_date("2024-03-01")
        self.plan_regenerate.action_generate_forecast_lines()
        self.assertEqual(len(self.plan_regenerate.forecast_line_ids), 3)
        self.assertFalse(
            self.env["mis.cash_flow.forecast_line"].browse(first_line_ids).exists()
        )

    def test_plan_generate_forecasts_limit_reached(self):
        self.company.cash_flow_plan_max_forecast_lines = 3
        self.plan_limit.action_generate_forecast_lines()
        self.assertEqual(len(self.plan_limit.forecast_line_ids), 3)

    def test_plan_forecast_line_count(self):
        self.assertEqual(self.plan_monthly.forecast_line_count, 0)
        self.plan_monthly.action_generate_forecast_lines()
        self.assertEqual(self.plan_monthly.forecast_line_count, 3)

    def test_plan_unlink_cascades_forecast_lines(self):
        self.plan_monthly.action_generate_forecast_lines()
        line_ids = self.plan_monthly.forecast_line_ids.ids
        self.plan_monthly.unlink()
        self.assertFalse(
            self.env["mis.cash_flow.forecast_line"].browse(line_ids).exists()
        )

    def check_matrix(self, args=None, ignore_rows=None):
        if not args:
            args = []
        if not ignore_rows:
            ignore_rows = []
        with mute_logger("odoo.addons.mis_builder.models.kpimatrix"):
            matrix = self.report._compute_matrix()
        for row in matrix.iter_rows():
            if row.kpi.name in ignore_rows:
                continue
            for cell in row.iter_cells():
                if not cell:
                    continue
                found = False
                label = cell.subcol.col.label
                for exp in args:
                    if exp[0] == row.kpi.name and exp[1] == label:
                        found = True
                        break
                if not found:
                    self.assertEqual(cell.val, 0)
