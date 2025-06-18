from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestLiquidityForecastReport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env["report.account_liquidity_forecast.liquidity_forecast"]
        self.company = self.env.user.company_id
        self.today = date.today()

        self.data = {
            "company_id": self.company.id,
            "date_from": (self.today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "date_to": self.today.strftime("%Y-%m-%d"),
            "period_length": "days",
            "only_posted_moves": True,
        }

    def test_generate_periods_days(self):
        """Test generation of daily periods with proper sequence and naming."""
        # Test with a 5-day range
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        data = {
            **self.data,
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "period_length": "days",
        }
        periods = self.report._generate_periods(data)
        self.assertEqual(len(periods), 5, "Should generate 5 daily periods")

        # Check sequences are continuous starting from 0
        sequences = [p["sequence"] for p in periods]
        self.assertEqual(
            sequences, [0, 1, 2, 3, 4], "Sequences should be continuous from 0"
        )

    def test_generate_periods_months(self):
        """Test generation of monthly periods with proper month boundaries."""
        # Test across multiple months
        start_date = date(2024, 1, 15)
        end_date = date(2024, 3, 10)
        data = {
            **self.data,
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "period_length": "months",
        }
        periods = self.report._generate_periods(data)
        self.assertEqual(len(periods), 3, "Should generate 3 monthly periods")
        self.assertIn(
            "Current", periods[0]["name"], "First period should contain 'Current'"
        )
        self.assertEqual(periods[0]["date_from"], date(2024, 1, 15))
        self.assertEqual(periods[0]["date_to"], date(2024, 1, 31))
        self.assertEqual(periods[1]["date_from"], date(2024, 2, 1))
        self.assertEqual(periods[1]["date_to"], date(2024, 2, 29))
        self.assertEqual(periods[2]["date_from"], date(2024, 3, 1))
        self.assertEqual(periods[2]["date_to"], date(2024, 3, 10))

    def test_generate_periods_leap_year_february(self):
        """Test monthly periods handle leap year February correctly."""
        # Test February in leap year
        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 29)
        data = {
            **self.data,
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "period_length": "months",
        }

        periods = self.report._generate_periods(data)

        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["date_from"], date(2024, 2, 1))
        self.assertEqual(periods[0]["date_to"], date(2024, 2, 29))

    def test_generate_periods_non_leap_year_february(self):
        """Test monthly periods handle non-leap year February correctly."""
        # Test February in non-leap year
        start_date = date(2023, 2, 1)
        end_date = date(2023, 2, 28)
        data = {
            **self.data,
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "period_length": "months",
        }

        periods = self.report._generate_periods(data)

        self.assertEqual(len(periods), 1)
        self.assertEqual(periods[0]["date_from"], date(2023, 2, 1))
        self.assertEqual(periods[0]["date_to"], date(2023, 2, 28))

    def test_generate_periods_year_boundary(self):
        """Test periods generation across year boundaries."""
        start_date = date(2023, 12, 15)
        end_date = date(2024, 1, 15)
        data = {
            **self.data,
            "date_from": start_date.strftime("%Y-%m-%d"),
            "date_to": end_date.strftime("%Y-%m-%d"),
            "period_length": "months",
        }

        periods = self.report._generate_periods(data)

        self.assertEqual(
            len(periods), 2, "Should generate 2 periods across year boundary"
        )

        # Check year boundary is handled correctly
        self.assertEqual(periods[0]["date_from"].year, 2023)
        self.assertEqual(periods[1]["date_from"].year, 2024)

    def test_complete_beginning_balance_initial(self):
        """Test beginning balance computed and set as float for initial empty periods."""
        periods = self.report._generate_periods(self.data)
        period = periods[0]
        period_seq = period["sequence"]
        liquidity_forecast_lines = [
            {"code": "beginning_balance", "periods": {period_seq: {}}}
        ]

        self.report._complete_beginning_balance(
            self.data, liquidity_forecast_lines, liquidity_forecast_lines[0], period
        )
        amount = liquidity_forecast_lines[0]["periods"][period_seq].get("amount")
        self.assertIsInstance(
            amount, float, "Beginning balance amount should be a float"
        )

    def test_complete_net_cash_flow(self):
        """Test net cash flow sums multiple cash flow lines correctly."""
        periods = self.report._generate_periods(self.data)
        period = periods[0]
        period_seq = period["sequence"]

        liquidity_forecast_lines = [
            {
                "code": "cash_flow_line_in_account_101",
                "periods": {period_seq: {"amount": 200.0}},
            },
            {
                "code": "cash_flow_line_out_account_202",
                "periods": {period_seq: {"amount": -50.0}},
            },
            {"code": "net_cash_flow", "periods": {period_seq: {}}},
        ]

        self.report._complete_net_cash_flow(
            self.data, liquidity_forecast_lines, liquidity_forecast_lines[2], period
        )
        amount = liquidity_forecast_lines[2]["periods"][period_seq].get("amount")
        self.assertEqual(
            amount, 150.0, "Net cash flow should be sum of cash in and cash out"
        )

    def test_handle_zero_and_negative_amounts(self):
        """Test proper handling of zero and negative cash flows."""
        periods = self.report._generate_periods(self.data)
        period = periods[0]
        period_seq = period["sequence"]

        liquidity_forecast_lines = [
            {
                "code": "cash_flow_line_in_account_101",
                "periods": {period_seq: {"amount": 0.0}},
            },
            {
                "code": "cash_flow_line_out_account_202",
                "periods": {period_seq: {"amount": -100.0}},
            },
            {"code": "net_cash_flow", "periods": {period_seq: {}}},
        ]

        self.report._complete_net_cash_flow(
            self.data, liquidity_forecast_lines, liquidity_forecast_lines[2], period
        )
        amount = liquidity_forecast_lines[2]["periods"][period_seq].get("amount")
        self.assertEqual(
            amount,
            -100.0,
            "Net cash flow should correctly handle zero and negative amounts",
        )
