# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# account_liquidity_forecast_purchase_stock/report/liquidity_forecast.py
from odoo import _, models


class LiquidityForecastReport(models.AbstractModel):
    _inherit = "report.account_liquidity_forecast.liquidity_forecast"

    def _prepare_liquidity_forecast_lines_period(
        self, data, liquidity_forecast_lines, period, periods
    ):
        res = super()._prepare_liquidity_forecast_lines_period(
            data, liquidity_forecast_lines, period, periods
        )
        self._prepare_cash_flow_lines_po_moves(
            data, liquidity_forecast_lines, period, periods
        )
        return res

    def _prepare_cash_flow_lines_po_moves(
        self, data, liquidity_forecast_lines, period, periods
    ):
        """Add stock moves to the liquidity forecast"""
        domain_move_states = ["confirmed", "waiting", "assigned"]

        from_date = periods[0]["date_from"]
        to_date = periods[-1]["date_to"]

        stock_moves = self.env["stock.move"].search(
            [
                ("state", "in", domain_move_states),
                ("purchase_line_id", "!=", False),
                ("company_id", "=", data["company_id"]),
                ("date", ">=", from_date),
                ("date", "<=", to_date),
            ]
        )

        code = "cash_flow_line_out_purchase_moves"
        lines = [line for line in liquidity_forecast_lines if line["code"] == code]
        if lines:
            flow_line = lines[0]
            # RESET amounts before recomputing
            for p_seq in flow_line["periods"]:
                flow_line["periods"][p_seq]["amount"] = 0.0
                flow_line["periods"][p_seq]["domain"] = ""
        else:
            flow_line = {
                "code": code,
                "type": "amount",
                "level": "detail",
                "model": "stock.move",
                "title": _("Scheduled Stock Moves"),
                "sequence": 3550,
                "periods": {
                    p["sequence"]: {"amount": 0.0, "domain": ""} for p in periods
                },
            }
            liquidity_forecast_lines.append(flow_line)

        move_ids_by_period = {p["sequence"]: [] for p in periods}

        for move in stock_moves:
            if not move.date:
                continue
            move_date = move.date.date() if hasattr(move.date, "date") else move.date

            for p in periods:
                if p["date_from"] <= move_date <= p["date_to"]:
                    po_line = move.purchase_line_id
                    price = po_line.price_unit
                    qty = move.product_qty
                    flow_line["periods"][p["sequence"]]["amount"] += -qty * price
                    move_ids_by_period[p["sequence"]].append(move.id)
                    break

        for seq, move_ids in move_ids_by_period.items():
            flow_line["periods"][seq]["domain"] = [("id", "in", move_ids)]

    def get_po_lines(self, data, period, periods):
        """Filter PO lines to exclude those already covered by stock moves or invoiced"""
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
            # Check if PO line is already covered by moves
            covered_by_move = False
            for move in line.move_ids.filtered(
                lambda m: m.state not in ("done", "cancel")
            ):
                if not move.date:
                    continue
                move_date = (
                    move.date.date() if hasattr(move.date, "date") else move.date
                )
                for p in periods:
                    if p["date_from"] <= move_date <= p["date_to"]:
                        covered_by_move = True
                        break
                if covered_by_move:
                    break

            if covered_by_move:
                continue  # already handled in _prepare_cash_flow_lines_po_moves

            # Check if there's uninvoiced quantity
            valid_invoice_lines = line.invoice_lines.filtered(
                lambda inv_line: inv_line.move_id.state not in ("draft", "cancel")
            )
            invoiced_qty = sum(valid_invoice_lines.mapped("quantity"))

            if line.product_qty > invoiced_qty:
                filtered_po_lines.append(line)

        return self.env["purchase.order.line"].browse(
            [line.id for line in filtered_po_lines]
        )
