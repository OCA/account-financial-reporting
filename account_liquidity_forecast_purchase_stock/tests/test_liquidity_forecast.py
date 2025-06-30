from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestLiquidityForecastPurchaseStock(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env["report.account_liquidity_forecast.liquidity_forecast"]
        self.company = self.env.user.company_id
        self.partner = self.env["res.partner"].create({"name": "Supplier Test"})

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
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

    def test_po_moves_added_to_forecast(self):
        """Test that stock moves from confirmed PO are added to liquidity forecast."""
        data = dict(self.wizard_data)

        # First run to get initial forecast values
        initial_lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_liquidity_forecast_lines_period(
            data, initial_lines, periods[0], periods
        )

        initial_po_moves = [
            line
            for line in initial_lines
            if line.get("code") == "cash_flow_line_out_purchase_moves"
        ]
        initial_amount = (
            initial_po_moves[0]["periods"][0]["amount"] if initial_po_moves else 0
        )

        # Create and confirm a purchase order
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "date_order": self.today,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": "PO Line",
                            "product_qty": 2.0,
                            "price_unit": 15.0,
                            "date_planned": self.today,
                        },
                    )
                ],
                "company_id": self.company.id,
            }
        )
        po.button_confirm()

        # Recompute report lines
        final_lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_liquidity_forecast_lines_period(
            data, final_lines, periods[0], periods
        )

        updated_po_moves = [
            line
            for line in final_lines
            if line.get("code") == "cash_flow_line_out_purchase_moves"
        ]

        self.assertTrue(
            updated_po_moves, "Expected PO moves line to be present in report"
        )

        final_amount = updated_po_moves[0]["periods"][0]["amount"]

        expected_delta = -30.0  # 2 units * 15 €/unit
        self.assertAlmostEqual(
            final_amount,
            initial_amount + expected_delta,
            msg=f"Expected PO move forecast to change by {expected_delta}",
        )
