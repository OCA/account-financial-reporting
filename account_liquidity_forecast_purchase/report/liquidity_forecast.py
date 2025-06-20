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
        self._prepare_cash_flow_lines_purchase_draft(
            data, liquidity_forecast_lines, period, periods
        )
        self._prepare_cash_flow_lines_purchase_not_received_not_billed(
            data, liquidity_forecast_lines, period, periods
        )
        self._prepare_cash_flow_lines_purchase_received_not_billed(
            data, liquidity_forecast_lines, period, periods
        )
        return res

    def _prepare_cash_flow_lines_purchase_draft(
        self, data, liquidity_forecast_lines, period, periods
    ):
        purchase_lines = self.get_po_lines_draft(data, period, periods)

        if not purchase_lines:
            return

        code = "cash_flow_line_out_purchase_draft"
        lines = [line for line in liquidity_forecast_lines if line["code"] == code]
        if lines:
            flow_line = lines[0]
        else:
            flow_line = {
                "code": code,
                "type": "amount",
                "level": "detail",
                "model": "purchase.order.line",
                "title": _("Draft PO"),
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

    def _prepare_cash_flow_lines_purchase_not_received_not_billed(
        self, data, liquidity_forecast_lines, period, periods
    ):
        purchase_lines = self.get_po_lines_not_received_not_billed(
            data, period, periods
        )

        if not purchase_lines:
            return

        code = "cash_flow_line_out_purchase_not_received_not_billed"
        lines = [line for line in liquidity_forecast_lines if line["code"] == code]
        if lines:
            flow_line = lines[0]
        else:
            flow_line = {
                "code": code,
                "type": "amount",
                "level": "detail",
                "model": "purchase.order.line",
                "title": _("Not Received Not Billed PO"),
                "sequence": 3550,
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

    def _prepare_cash_flow_lines_purchase_received_not_billed(
        self, data, liquidity_forecast_lines, period, periods
    ):
        # Get PO lines with pending invoicing
        purchase_lines = self.get_po_lines_received_not_billed(data, period, periods)

        if not purchase_lines:
            return

        code = "cash_flow_line_out_purchase_received_not_billed"
        lines = [line for line in liquidity_forecast_lines if line["code"] == code]
        if lines:
            flow_line = lines[0]
        else:
            flow_line = {
                "code": code,
                "type": "amount",
                "level": "detail",
                "model": "purchase.order.line",
                "title": _("Received Not Billed PO"),
                "sequence": 3500,
                "periods": {
                    p["sequence"]: {"amount": 0.0, "domain": ""} for p in periods
                },
            }
            liquidity_forecast_lines.append(flow_line)

        total = 0.0
        line_ids = []

        for po_line, remaining_qty in purchase_lines:
            # Proportional subtotal based on uninvoiced qty
            if po_line.product_qty:
                total += po_line.price_unit * remaining_qty
                line_ids.append(po_line.id)

        flow_line["periods"][period["sequence"]]["amount"] += -total
        flow_line["periods"][period["sequence"]]["domain"] = [("id", "in", line_ids)]

    def get_po_lines_draft(self, data, period, periods):
        states = ["draft", "sent"]

        domain = [
            ("state", "in", states),
            ("date_planned", "<=", period["date_to"]),
            ("company_id", "=", data.get("company_id", self.env.company.id)),
        ]
        if period["sequence"] > 0:
            domain += [("date_planned", ">=", period["date_from"])]

        po_lines = self.env["purchase.order.line"].search(domain)

        return po_lines

    def get_po_lines_not_received_not_billed(self, data, period, periods):
        states = ["to approve", "purchase", "done"]

        domain = [
            ("state", "in", states),
            ("qty_received", "=", 0),
            ("date_planned", "<=", period["date_to"]),
            ("company_id", "=", data.get("company_id", self.env.company.id)),
        ]
        if period["sequence"] > 0:
            domain += [("date_planned", ">=", period["date_from"])]

        po_lines = self.env["purchase.order.line"].search(domain)

        # Filter out lines with any billed quantity (invoices not in draft/cancel)
        result = po_lines.filtered(
            lambda line: not line.invoice_lines.filtered(
                lambda inv_line: inv_line.move_id.state not in ("draft", "cancel")
            )
        )
        return result

    def get_po_lines_received_not_billed(self, data, period, periods):
        states = ["to approve", "purchase", "done"]

        domain = [
            ("state", "in", states),
            ("qty_received", ">", 0),
            ("date_planned", "<=", period["date_to"]),
            ("company_id", "=", data.get("company_id", self.env.company.id)),
        ]
        if period["sequence"] > 0:
            domain += [("date_planned", ">=", period["date_from"])]

        po_lines = self.env["purchase.order.line"].search(domain)

        results = []
        for line in po_lines:
            valid_invoice_lines = line.invoice_lines.filtered(
                lambda inv_line: inv_line.move_id.state not in ("draft", "cancel")
            )
            invoiced_qty = sum(valid_invoice_lines.mapped("quantity"))
            remaining_qty = line.qty_received - invoiced_qty

            if remaining_qty > 0:
                results.append((line, remaining_qty))

        return results
