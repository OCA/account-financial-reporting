# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends("purchase_line_id")
    def _compute_currency_id(self):
        non_purchase_move = self.env["stock.move"]
        for move in self:
            if move.purchase_line_id:
                move.currency_id = move.purchase_line_id.currency_id
            else:
                non_purchase_move |= move
        if non_purchase_move:
            return super(StockMove, non_purchase_move)._compute_currency_id()

    def get_quantity_invoiced(self, invoice_lines):
        if self.purchase_line_id:
            if not invoice_lines:
                return 0
            qty_invoiced = abs(
                sum(
                    invoice_lines.mapped(
                        lambda line: line.quantity
                        if (
                            line.move_id.move_type == "in_invoice"
                            and not self.to_refund
                        )
                        or (line.move_id.move_type == "in_refund" and self.to_refund)
                        else -line.quantity
                    )
                )
            )
            # Check when grouping different moves in an invoice line
            moves = invoice_lines.mapped("move_line_ids")
            date_start = self.env.context.get("moves_date_start")
            date_end = self.env.context.get("moves_date_end")
            if date_start and date_end:
                moves = moves.filtered(
                    lambda ml: ml.state == "done"
                    and (ml.date_done >= date_start and ml.date_done <= date_end)
                )
            total_qty = moves.get_total_devolution_moves()
            if qty_invoiced != total_qty:
                invoiced = 0.0
                for move in moves:
                    qty = (
                        move.quantity
                        if move.quantity <= (qty_invoiced - invoiced)
                        else qty_invoiced - invoiced
                    )
                    if move.check_is_return():
                        qty = -qty
                    if move == self:
                        return qty
                    invoiced += qty
                return 0
            return self.quantity if not self.check_is_return() else -self.quantity
        return super().get_quantity_invoiced(invoice_lines)

    def _set_not_invoiced_values(self, qty_to_invoice, invoiced_qty):
        self.ensure_one()
        if self.purchase_line_id:
            self.quantity_not_invoiced = qty_to_invoice - invoiced_qty
            price_unit = self.purchase_line_id.price_unit
            if "discount" in self.purchase_line_id._fields:
                price_unit = self.purchase_line_id.price_unit * (
                    1 - self.purchase_line_id.discount / 100
                )
            self.price_not_invoiced = (qty_to_invoice - invoiced_qty) * price_unit
        else:
            return super()._set_not_invoiced_values(qty_to_invoice, invoiced_qty)

    @api.depends("purchase_line_id")
    @api.depends_context("date_check_invoiced_moves")
    def _compute_not_invoiced_values(self):
        return super()._compute_not_invoiced_values()

    def _get_model_id_origin_document(self):
        if not self.purchase_line_id:
            return super()._get_model_id_origin_document()
        return self.purchase_line_id.order_id._name, self.purchase_line_id.order_id.id
