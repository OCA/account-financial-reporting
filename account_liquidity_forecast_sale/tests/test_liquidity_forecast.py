from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestLiquidityForecastSale(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = self.env["report.account_liquidity_forecast.liquidity_forecast"]
        self.company = self.env.user.company_id
        self.partner_1 = self.env["res.partner"].create({"name": "Test Partner 1"})

        self.product_1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "standard_price": 10.0,
                "list_price": 15.0,
            }
        )

        self.product_2 = self.env["product.product"].create(
            {
                "name": "Test Product 2",
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
            "include_so_draft": True,
        }

        # Create draft sale order
        self.so_draft_1 = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
                "date_order": self.today,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_1.id,
                            "name": "Draft SO Line",
                            "product_uom_qty": 5.0,
                            "price_unit": 20.0,
                        },
                    )
                ],
                "company_id": self.company.id,
            }
        )

        # Create confirmed sale order
        self.so_confirm = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
                "date_order": self.today,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_2.id,
                            "name": "Confirmed SO Line",
                            "product_uom_qty": 3.0,
                            "price_unit": 30.0,
                        },
                    )
                ],
                "company_id": self.company.id,
            }
        )
        self.so_confirm.action_confirm()

    def test_draft_sale_order_included_when_flag_set(self):
        """Test that draft SOs are included when include_so_draft=True."""
        data = dict(self.wizard_data)

        lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_cash_flow_lines_sale_draft(
            data, lines, periods[0], periods
        )

        draft_lines = [
            line
            for line in lines
            if line.get("code") == "cash_flow_line_out_sale_draft"
        ]
        self.assertTrue(
            draft_lines,
            "Expected draft sale order lines to be included in forecast lines",
        )

        self.assertEqual(
            draft_lines[0]["periods"][0]["amount"], 100.0, "Amount does not match"
        )

    def test_draft_sale_order_not_included_when_flag_false(self):
        """Test that draft SOs are not included when include_so_draft=False."""
        data = dict(self.wizard_data)
        data["include_so_draft"] = False

        lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_liquidity_forecast_lines_period(
            data, lines, periods[0], periods
        )

        draft_lines = [
            line
            for line in lines
            if line.get("code") == "cash_flow_line_out_sale_draft"
        ]
        self.assertFalse(
            draft_lines,
            "Draft sale order lines should not be included when flag is False",
        )

    def test_confirmed_sale_order_not_included_in_draft_lines(self):
        """Test that confirmed SOs are not included in draft lines."""
        data = dict(self.wizard_data)

        lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_cash_flow_lines_sale_draft(
            data, lines, periods[0], periods
        )

        draft_lines = [
            line
            for line in lines
            if line.get("code") == "cash_flow_line_out_sale_draft"
        ]

        self.assertTrue(draft_lines, "Should have draft lines from draft SO")

        domain_ids = draft_lines[0]["periods"][0]["domain"][0][2]
        self.assertIn(
            self.so_draft_1.id,
            domain_ids,
            "Domain should contain the draft SO ID",
        )
        self.assertNotIn(
            self.so_confirm.id,
            domain_ids,
            "Domain should NOT contain the confirmed SO ID",
        )

    def test_multiple_draft_sale_orders_aggregated(self):
        """Test that multiple draft SOs are properly aggregated."""
        # Create additional draft SO
        so_draft_2 = self.env["sale.order"].create(
            {
                "partner_id": self.partner_1.id,
                "date_order": self.today,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_2.id,
                            "name": "Additional Draft Line",
                            "product_uom_qty": 2.0,
                            "price_unit": 15.0,
                        },
                    )
                ],
                "company_id": self.company.id,
            }
        )

        data = dict(self.wizard_data)
        lines = []
        periods = self.report._generate_periods(data)
        self.report._prepare_cash_flow_lines_sale_draft(
            data, lines, periods[0], periods
        )

        draft_lines = [
            line
            for line in lines
            if line.get("code") == "cash_flow_line_out_sale_draft"
        ]
        self.assertEqual(
            len(draft_lines),
            1,
            "Should have only one draft line aggregating all draft SOs",
        )

        expected_total = 100.0 + 30.0
        self.assertEqual(
            draft_lines[0]["periods"][0]["amount"],
            expected_total,
            f"Total amount should be {expected_total}",
        )

        domain_ids = draft_lines[0]["periods"][0]["domain"][0][2]
        self.assertIn(self.so_draft_1.id, domain_ids)
        self.assertIn(so_draft_2.id, domain_ids)
