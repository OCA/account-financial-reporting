from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestLiquidityForecastPurchase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env["report.account_liquidity_forecast.liquidity_forecast"]
        self.company = self.env.user.company_id
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner 1"})

        self.product_1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "standard_price": 20.0,
                "list_price": 25.0,
            }
        )

        self.today = date.today()
        self.date_to = self.today + timedelta(days=30)

        self.wizard_data = {
            "company_id": self.company.id,
            "date_from": self.today.strftime("%Y-%m-%d"),
            "date_to": self.date_to.strftime("%Y-%m-%d"),
            "period_length": "days",
            "only_posted_moves": True,
            "include_po_draft": True,
        }

    def test_multiple_purchase_orders_aggregated(self):
        """Test that multiple draft POs are properly aggregated."""
        data = dict(self.wizard_data)

        # First, get the initial report amount before adding the new PO
        initial_lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_cash_flow_lines_purchase(
            data, initial_lines, periods[0], periods
        )

        initial_purchase = [
            line
            for line in initial_lines
            if line.get("code") == "cash_flow_line_out_purchase"
        ]
        initial_report_amount = (
            initial_purchase[0]["periods"][0]["amount"] if initial_purchase else 0
        )

        # Create additional draft PO for this test
        self.env["purchase.order"].create(
            {
                "partner_id": self.partner_1.id,
                "date_order": self.today,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_1.id,
                            "name": "Additional Draft Line",
                            "product_qty": 2.0,
                            "price_unit": 15.0,
                            "date_planned": self.today,
                        },
                    )
                ],
                "company_id": self.company.id,
            }
        )

        lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_cash_flow_lines_purchase(data, lines, periods[0], periods)

        purchase = [
            line for line in lines if line.get("code") == "cash_flow_line_out_purchase"
        ]

        expected_total = initial_report_amount + (-30.0)
        self.assertEqual(
            purchase[0]["periods"][0]["amount"],
            expected_total,
            f"Total amount should be {expected_total}",
        )
