# © 2026 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "prruebaaas")
class TestCashFlowExtended(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "TEST"})
        cls.account = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "code": "TEST1",
                "name": "Account",
                "account_type": "asset_cash",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        cls.category_parent = cls.env["mis.cash.flow.forecast.category"].create(
            {"name": "Parent"}
        )
        cls.category_child = cls.env["mis.cash.flow.forecast.category"].create(
            {"name": "Child", "parent_id": cls.category_parent.id}
        )
        cls.line_with_category = cls.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": cls.account.id,
                "date": Date.today(),
                "balance": 100,
                "company_id": cls.company.id,
                "category_id": cls.category_child.id,
            }
        )
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
                "category_id": cls.category_child.id,
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

    def test_category_complete_name(self):
        self.category_parent.name = "Root"
        self.assertEqual(self.category_child.complete_name, "Root / Child")

    def test_category_unlink_sets_forecast_line_category_null(self):
        self.category_child.unlink()
        self.assertFalse(self.line_with_category.category_id)

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
