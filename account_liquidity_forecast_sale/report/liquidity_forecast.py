# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class LiquidityForecastReport(models.AbstractModel):
    _inherit = "report.account_liquidity_forecast.liquidity_forecast"

    def _prepare_liquidity_forecast_lines_period(
        self, data, liquidity_forecast_lines, period, periods
    ):
        res = super()._prepare_liquidity_forecast_lines_period(
            data, liquidity_forecast_lines, period, periods
        )
        include_so_draft = data.get("include_so_draft", False)
        if include_so_draft:
            self._prepare_cash_flow_lines_sale_draft(
                data, liquidity_forecast_lines, period, periods
            )
        return res

    def _prepare_cash_flow_lines_sale_draft(
        self, data, liquidity_forecast_lines, period, periods
    ):
        domain = self.get_so_domain(period)

        draft_sale_orders = self.env["sale.order"].search(domain)
        if not draft_sale_orders:
            return

        sale_lines = draft_sale_orders.mapped("order_line")
        if not sale_lines:
            return

        code = "cash_flow_line_out_sale_draft"
        existing_lines = [
            line for line in liquidity_forecast_lines if line["code"] == code
        ]

        if existing_lines:
            flow_line = existing_lines[0]
        else:
            flow_line = {
                "code": code,
                "type": "amount",
                "level": "detail",
                "model": "sale.order.line",
                "title": _("Draft Sale Orders"),
                "sequence": 3500,
                "periods": {
                    p["sequence"]: {"amount": 0.0, "domain": []} for p in periods
                },
            }
            liquidity_forecast_lines.append(flow_line)

        total = sum(sale_line.price_subtotal for sale_line in sale_lines)
        flow_line["periods"][period["sequence"]]["amount"] += total
        flow_line["periods"][period["sequence"]]["domain"] = [
            ("id", "in", sale_lines.ids)
        ]

    def get_so_domain(self, period):
        domain = [
            ("state", "in", ["draft", "sent"]),
            ("date_order", "<=", period["date_to"]),
        ]
        if period["sequence"] > 0:
            domain.append(("date_order", ">=", period["date_from"]))
        return domain
