# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.tools import float_is_zero


class AccountSaleStockReportNonBilledWiz(models.TransientModel):
    _name = "account.sale.stock.report.non.billed.wiz"
    _description = "Wizard to open stock moves that have not been invoiced at that time"

    def _default_stock_move_non_billed_threshold(self):
        return self.env.company.stock_move_non_billed_threshold

    stock_move_non_billed_threshold = fields.Date(
        default=lambda self: self._default_stock_move_non_billed_threshold()
    )
    date_check = fields.Date(string="Date", default=fields.Date.today)
    interval_restrict_invoices = fields.Boolean(
        string="Restrict invoices using the date interval"
    )

    def _get_search_domain(self):
        return [
            ("date_done", ">=", self.stock_move_non_billed_threshold),
            ("date_done", "<=", self.date_check),
            ("sale_line_id", "!=", False),
            ("state", "=", "done"),
            ("scrapped", "=", False),
            "|",
            ("location_dest_id.usage", "=", "customer"),
            "&",
            ("location_id.usage", "=", "customer"),
            ("to_refund", "=", True),
        ]

    @api.model
    def discart_kits_from_moves(self, stock_moves):
        return stock_moves.filtered(
            lambda move: move.product_id == move.sale_line_id.product_id
        )

    @api.model
    def _get_neutralized_moves(self, stock_moves):
        neutralized_moves = self.env["stock.move"]
        for move in stock_moves.sorted("origin_returned_move_id"):
            # Not show returns that not update qty on stock
            if move.origin_returned_move_id and not move.to_refund:
                neutralized_moves |= move
            if move in neutralized_moves:
                continue
            dp = self.env["decimal.precision"].precision_get("Product Unit of Measure")
            date_start = (
                self.stock_move_non_billed_threshold
                if self.interval_restrict_invoices
                else False
            )
            if float_is_zero(
                move.quantity - sum(move.returned_move_ids.mapped("quantity")),
                precision_digits=dp,
            ) and not (
                move.invoice_line_ids
                + move.returned_move_ids.mapped("invoice_line_ids")
            ).filtered(
                lambda line, date_start=date_start: line.check_invoice_line_in_date(
                    self.date_check, date_start=date_start
                )
            ):
                neutralized_moves |= move + move.returned_move_ids
        return neutralized_moves

    def open_at_date(self):
        dp = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        # Get the moves after the threshold
        domain = self._get_search_domain()
        stock_moves = self.env["stock.move"].search(domain)
        stock_moves = self.discart_kits_from_moves(stock_moves)
        stock_moves -= self._get_neutralized_moves(stock_moves)
        final_stock_move_ids = []
        date_start = (
            self.stock_move_non_billed_threshold
            if self.interval_restrict_invoices
            else False
        )
        for move in stock_moves:
            inv_lines_not_cancel = move.invoice_line_ids.filtered(
                lambda line: line.move_id.state != "cancel"
            )
            moves_in_date = inv_lines_not_cancel.move_line_ids.filtered(
                lambda m: m.state == "done"
                and m.date_done >= self.stock_move_non_billed_threshold
                and m.date_done <= self.date_check
            )
            inv_lines = moves_in_date.invoice_line_ids.filtered(
                lambda line: line.check_invoice_line_in_date(
                    self.date_check, date_start=date_start
                )
            )
            qty_to_invoice = (
                move.quantity if not move.check_is_return() else -move.quantity
            )
            calculated_qty = move.with_context(
                moves_date_start=self.stock_move_non_billed_threshold,
                moves_date_end=self.date_check,
            ).get_quantity_invoiced(inv_lines)
            if not float_is_zero(qty_to_invoice - calculated_qty, precision_digits=dp):
                final_stock_move_ids.append(move.id)
        tree_view_id = self.env.ref(
            "account_sale_stock_report_non_billed.view_move_tree"
        ).id
        pivot_view_id = self.env.ref(
            "account_sale_stock_report_non_billed.view_move_pivot_no_invoiced"
        ).id
        search_view_id = self.env.ref(
            "account_sale_stock_report_non_billed.view_move_search"
        ).id
        context = dict(
            self.env.context,
            non_billed_date=self.date_check,
            non_billed_date_start=self.stock_move_non_billed_threshold,
        )
        if self.interval_restrict_invoices:
            context = dict(
                context,
                non_billed_invoice_date_start=self.stock_move_non_billed_threshold,
            )
        action = {
            "type": "ir.actions.act_window",
            "views": [(tree_view_id, "tree"), (pivot_view_id, "pivot")],
            "view_mode": "tree,pivot",
            "search_view_id": search_view_id,
            "name": _("Non billed moves (%(from)s -> %(to)s)")
            % {"from": self.stock_move_non_billed_threshold, "to": self.date_check},
            "res_model": "stock.move",
            "domain": [("id", "in", final_stock_move_ids)],
            "context": context,
        }
        return action
