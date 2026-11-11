# Copyright 2022 Tecnativa - Carlos Roca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.fields import Domain

# Fields that can't be aggregated by the ORM (they are computed in Python and depend on
# the context), so they need the special treatment done in the read group overrides.
NON_BILLED_AGGREGATE_FIELDS = ("quantity_not_invoiced", "price_not_invoiced")


class StockMove(models.Model):
    _inherit = "stock.move"

    quantity_not_invoiced = fields.Float(
        string="Qty. to invoice",
        compute="_compute_not_invoiced_values",
        digits="Product Unit of Measure",
        compute_sudo=True,
    )
    price_not_invoiced = fields.Float(
        string="Amount to invoice",
        compute="_compute_not_invoiced_values",
        digits="Product Price",
        compute_sudo=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", compute="_compute_currency_id", compute_sudo=True
    )
    # The report works with dates, not with datetimes, so we need the validation day
    # expressed in the user time zone to be able to filter and group by it. It's stored
    # for being usable in domains and group bys. It's pre-computed in SQL on install by
    # the module pre_init_hook to avoid a massive recomputation on big databases.
    date_done = fields.Date(
        string="Effective Date", compute="_compute_date_done", store=True, index=True
    )

    @api.depends("picking_id.date_done")
    def _compute_date_done(self):
        self.date_done = False
        for move in self:
            if move.picking_id.date_done:
                # Convert to the user time zone, as the raw datetime is stored in UTC
                # and the day could be shifted otherwise.
                move.date_done = fields.Datetime.context_timestamp(
                    move, move.picking_id.date_done
                ).date()

    @api.depends("sale_line_id")
    def _compute_currency_id(self):
        """Method to be overwritten when new implementations are made, e.g. with
        purchase_stock_picking_invoice_link.
        """
        self.currency_id = False
        for move in self:
            if move.sale_line_id:
                move.currency_id = move.sale_line_id.currency_id

    def check_is_return(self):
        self.ensure_one()
        if not self.origin_returned_move_id:
            return False
        else:
            return not self.origin_returned_move_id.check_is_return()

    def get_total_devolution_moves(self):
        total_qty = 0
        for move in self:
            # Avoid moves related to returns that not update qty on stock
            if move.origin_returned_move_id and not move.to_refund:
                continue
            if not move.check_is_return():
                total_qty += move.quantity
            else:
                total_qty -= move.quantity
        return total_qty

    def get_quantity_invoiced(self, invoice_lines):
        if not invoice_lines:
            return 0
        total_invoiced = abs(
            sum(
                invoice_lines.mapped(
                    lambda line: line.quantity
                    if (line.move_id.move_type == "out_invoice" and not self.to_refund)
                    or (line.move_id.move_type == "out_refund" and self.to_refund)
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
        self.quantity_not_invoiced = qty_to_invoice - invoiced_qty
        self.price_not_invoiced = (
            qty_to_invoice - invoiced_qty
        ) * self.sale_line_id.price_reduce_taxexcl

    @api.depends("sale_line_id")
    @api.depends_context(
        "non_billed_date", "non_billed_date_start", "non_billed_invoice_date_start"
    )
    def _compute_not_invoiced_values(self):
        for move in self:
            context = self.env.context
            if not context.get("non_billed_date") or not context.get(
                "non_billed_date_start"
            ):
                move.quantity_not_invoiced = 0
                move.price_not_invoiced = 0
                continue
            date_start = fields.Date.from_string(context["non_billed_date_start"])
            date_end = fields.Date.from_string(context["non_billed_date"])
            invoices_not_cancel = move.invoice_line_ids.filtered(
                lambda line: line.move_id.state != "cancel"
            )
            moves_in_date = invoices_not_cancel.mapped("move_line_ids").filtered(
                lambda m, date_start=date_start, date_end=date_end: m.state == "done"
                and m.date_done >= date_start
                and m.date_done <= date_end
            )
            invoice_date_start = False
            if context.get("non_billed_invoice_date_start"):
                invoice_date_start = fields.Date.from_string(
                    context["non_billed_invoice_date_start"]
                )
            inv_lines = moves_in_date.mapped("invoice_line_ids").filtered(
                lambda line,
                date_end=date_end,
                invoice_date_start=invoice_date_start: line.check_invoice_line_in_date(
                    date_end,
                    date_start=invoice_date_start,
                )
            )
            qty_to_invoice = (
                move.quantity if not move.check_is_return() else -move.quantity
            )
            calculated_qty = move.with_context(
                moves_date_start=date_start,
                moves_date_end=date_end,
            ).get_quantity_invoiced(inv_lines)
            move._set_not_invoiced_values(qty_to_invoice, calculated_qty)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Advertise a 'sum' aggregator for our non stored fields.

        The ORM can't build any SQL aggregate for them, so it reports no aggregator at
        all and both the list and the pivot views would refuse to use them as measures.
        The aggregation itself is done in Python in the read group overrides below.
        """
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if attributes is not None and "aggregator" not in attributes:
            return res
        for fname in NON_BILLED_AGGREGATE_FIELDS:
            if fname in res:
                res[fname]["aggregator"] = "sum"
        return res

    @api.model
    def _split_non_billed_aggregates(self, aggregates):
        """Split the requested aggregates into the ones the ORM can handle and the ones
        we have to compute in Python.
        """
        sql_aggregates = []
        python_aggregates = []
        for spec in aggregates:
            if spec.split(":")[0] in NON_BILLED_AGGREGATE_FIELDS:
                python_aggregates.append(spec)
            else:
                sql_aggregates.append(spec)
        return sql_aggregates, python_aggregates

    def _apply_non_billed_aggregates(self, domain, groups, aggregates):
        """Add the sum of the given non stored aggregates to each formatted group."""
        if not aggregates:
            return
        for group in groups:
            moves = self.search(Domain.AND([domain, group["__extra_domain"]]))
            for spec in aggregates:
                group[spec] = sum(moves.mapped(spec.split(":")[0]))

    @api.model
    def formatted_read_group(
        self,
        domain,
        groupby=(),
        aggregates=(),
        having=(),
        offset=0,
        limit=None,
        order=None,
    ):
        """Feed the grouped list view with the values computed in Python."""
        sql_aggregates, python_aggregates = self._split_non_billed_aggregates(
            aggregates
        )
        groups = super().formatted_read_group(
            domain,
            groupby,
            sql_aggregates,
            having=having,
            offset=offset,
            limit=limit,
            order=order,
        )
        self._apply_non_billed_aggregates(domain, groups, python_aggregates)
        return groups

    @api.model
    def formatted_read_grouping_sets(
        self, domain, grouping_sets, aggregates=(), *, order=None
    ):
        """Feed the pivot view with the values computed in Python."""
        sql_aggregates, python_aggregates = self._split_non_billed_aggregates(
            aggregates
        )
        groups_list = super().formatted_read_grouping_sets(
            domain, grouping_sets, sql_aggregates, order=order
        )
        for groups in groups_list:
            self._apply_non_billed_aggregates(domain, groups, python_aggregates)
        return groups_list

    def _get_model_id_origin_document(self):
        if not self.sale_line_id:
            return
        return self.sale_line_id.order_id._name, self.sale_line_id.order_id.id

    def open_origin_document(self):
        model, res_id = self._get_model_id_origin_document()
        return {
            "type": "ir.actions.act_window",
            "views": [(False, "form")],
            "view_mode": "form",
            "res_model": model,
            "res_id": res_id,
            "context": self.env.context,
        }
