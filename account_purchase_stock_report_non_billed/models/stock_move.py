# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends("purchase_line_id")
    def _compute_currency_id(self):
        purchase_moves = self.filtered("purchase_line_id")
        for move in purchase_moves:
            move.currency_id = move.purchase_line_id.currency_id
        return super(StockMove, self - purchase_moves)._compute_currency_id()

    def get_quantity_invoiced(self, invoice_lines):
        if not self.purchase_line_id:
            return super().get_quantity_invoiced(invoice_lines)
        if not invoice_lines:
            return 0
        total_invoiced = abs(
            sum(
                invoice_lines.mapped(
                    lambda line: line.quantity
                    if (line.move_id.move_type == "in_invoice" and not self.to_refund)
                    or (line.move_id.move_type == "in_refund" and self.to_refund)
                    else -line.quantity
                )
            )
        )
        # Check when grouping different moves in an invoice line
        moves = invoice_lines.move_line_ids.filtered(lambda x: x.state == "done")
        date_start = self.env.context.get("moves_date_start")
        date_end = self.env.context.get("moves_date_end")
        if date_start and date_end:
            moves = moves.filtered(
                lambda ml: ml.date_done >= date_start and ml.date_done <= date_end
            )
        total_qty = moves.get_total_devolution_moves()
        if total_invoiced != total_qty:
            invoiced = 0.0
            for move in moves:
                qty = (
                    move.quantity
                    if move.quantity <= (total_invoiced - invoiced)
                    else total_invoiced - invoiced
                )
                if move.check_is_return():
                    qty = -qty
                if move == self:
                    return qty
                invoiced += qty
            return 0
        return self.quantity if not self.check_is_return() else -self.quantity

    def _set_not_invoiced_values(self, qty_to_invoice, invoiced_qty):
        self.ensure_one()
        if not self.purchase_line_id:
            return super()._set_not_invoiced_values(qty_to_invoice, invoiced_qty)
        self.quantity_not_invoiced = qty_to_invoice - invoiced_qty
        self.price_not_invoiced = (
            qty_to_invoice - invoiced_qty
        ) * self.purchase_line_id.price_unit_discounted

    @api.depends("purchase_line_id")
    def _compute_not_invoiced_values(self):
        return super()._compute_not_invoiced_values()

    def _get_model_id_origin_document(self):
        if not self.purchase_line_id:
            return super()._get_model_id_origin_document()
        return self.purchase_line_id.order_id._name, self.purchase_line_id.order_id.id
