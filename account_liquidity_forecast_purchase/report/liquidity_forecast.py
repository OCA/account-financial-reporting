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
        self._prepare_cash_flow_lines_purchase(
            data, liquidity_forecast_lines, period, periods
        )
        return res

    def _prepare_cash_flow_lines_purchase(
        self, data, liquidity_forecast_lines, period, periods
    ):

        purchase_lines = self.get_po_lines(data, period, periods)

        if not purchase_lines:
            return

        code = "cash_flow_line_out_purchase"
        lines = [line for line in liquidity_forecast_lines if line["code"] == code]
        if lines:
            flow_line = lines[0]
        else:
            flow_line = {
                "code": code,
                "type": "amount",
                "level": "detail",
                "model": "purchase.order.line",
                "title": _("Purchase Orders"),
                "sequence": 3500,
                "periods": {
                    p["sequence"]: {"amount": 0.0, "domain": ""} for p in periods
                },
            }
            liquidity_forecast_lines.append(flow_line)

        total = 0.0
        line_ids = purchase_lines.ids
        for po_line in purchase_lines:
            total += po_line.price_subtotal

        flow_line["periods"][period["sequence"]]["amount"] += -total
        flow_line["periods"][period["sequence"]]["domain"] = [("id", "in", line_ids)]

    def get_po_lines(self, data, period, periods):
        states = ["sent", "to approve", "purchase", "done"]
        if data.get("include_po_draft", False):
            states.append("draft")

        domain = [
            ("state", "in", states),
            ("date_planned", "<=", period["date_to"]),
        ]
        if period["sequence"] > 0:
            domain += [("date_planned", ">=", period["date_from"])]

        po_lines = self.env["purchase.order.line"].search(domain)

        filtered_po_lines = []
        for line in po_lines:
            valid_invoice_lines = line.invoice_lines.filtered(
                lambda inv_line: inv_line.move_id.state not in ("draft", "cancel")
            )
            invoiced_qty = sum(valid_invoice_lines.mapped("quantity"))
            if line.product_qty > invoiced_qty:
                filtered_po_lines.append(line)

        po_lines = po_lines.browse([line.id for line in filtered_po_lines])

        return po_lines
