# Copyright 2026 PT Solusi Aglis Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo import api, fields, models
from odoo.tools import float_round

_logger = logging.getLogger(__name__)

# Journal types treated as cash basis (direct copy)
CASH_BASIS_JOURNAL_TYPES = ("bank", "cash", "general")


class CashBasisMoveLine(models.Model):
    _name = "cash.basis.move.line"
    _description = "Cash Basis Journal Item"
    _order = "date desc, id desc"

    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Journal Item",
        index=True,
        ondelete="cascade",
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        index=True,
        ondelete="cascade",
    )
    partial_reconcile_id = fields.Many2one(
        comodel_name="account.partial.reconcile",
        string="Partial Reconciliation",
        index=True,
        ondelete="cascade",
    )
    date = fields.Date(string="Date", index=True)
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        index=True,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        index=True,
    )
    name = fields.Char(string="Label")
    ref = fields.Char(string="Reference")
    debit = fields.Float(string="Debit", digits="Account")
    credit = fields.Float(string="Credit", digits="Account")
    balance = fields.Float(string="Balance", digits="Account")
    amount_currency = fields.Float(string="Amount in Currency", digits="Account")
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
    )
    tax_line_id = fields.Many2one(
        comodel_name="account.tax",
        string="Originator Tax",
    )
    reconcile_percentage = fields.Float(
        string="Reconcile %",
        digits=(16, 4),
    )

    @api.model
    def _cron_generate_cash_basis_lines(self):
        """Generate cash basis journal items from two sources:
        1. Direct copy from cash basis journals
        2. Proportional recognition on reconciliation
        """
        self._generate_direct_copy_lines()
        self._generate_reconciliation_lines()

    @api.model
    def _prepare_cash_basis_line_vals(
        self, line, date, partial=False, percentage=100.0
    ):
        """Prepare values for a cash basis move line."""
        factor = percentage / 100.0
        company_currency = line.company_id.currency_id
        prec = company_currency.rounding
        debit = float_round(line.debit * factor, precision_rounding=prec)
        credit = float_round(line.credit * factor, precision_rounding=prec)
        return {
            "move_line_id": line.id,
            "move_id": line.move_id.id,
            "partial_reconcile_id": partial.id if partial else False,
            "date": date,
            "account_id": line.account_id.id,
            "partner_id": line.partner_id.id,
            "journal_id": line.journal_id.id,
            "name": line.name,
            "ref": line.ref,
            "debit": debit,
            "credit": credit,
            "balance": float_round(debit - credit, precision_rounding=prec),
            "amount_currency": float_round(
                line.amount_currency * factor, precision_rounding=prec
            ),
            "currency_id": line.currency_id.id,
            "company_id": line.company_id.id,
            "product_id": line.product_id.id,
            "analytic_account_id": line.analytic_account_id.id,
            "tax_line_id": line.tax_line_id.id,
            "reconcile_percentage": percentage,
            # Used for rounding adjustment, not stored in DB
            "_account_internal_type": line.account_id.internal_type,
        }

    @api.model
    def _generate_direct_copy_lines(self):
        """Source 1: Direct copy from cash basis journals."""
        # Find already-processed move IDs via SQL (avoids loading records)
        self.env.cr.execute(
            """
            SELECT DISTINCT move_id FROM cash_basis_move_line
            WHERE partial_reconcile_id IS NULL
        """
        )
        existing_move_ids = [r[0] for r in self.env.cr.fetchall()]
        # Search only unprocessed moves directly in the domain
        moves = self.env["account.move"].search(
            [
                ("state", "=", "posted"),
                ("journal_id.type", "in", CASH_BASIS_JOURNAL_TYPES),
                ("id", "not in", existing_move_ids),
            ]
        )
        vals_list = []
        for move in moves:
            for line in move.line_ids:
                vals_list.append(
                    self._prepare_cash_basis_line_vals(
                        line, move.date, percentage=100.0
                    )
                )
        if vals_list:
            self._strip_internal_keys(vals_list)
            self.sudo().create(vals_list)
            _logger.info(
                "Cash basis: created %d direct copy lines from %d moves.",
                len(vals_list),
                len(moves),
            )

    @api.model
    def _generate_reconciliation_lines(self):
        """Source 2: Proportional recognition on reconciliation."""
        # Find already-processed partial IDs via SQL (avoids loading records)
        self.env.cr.execute(
            """
            SELECT DISTINCT partial_reconcile_id FROM cash_basis_move_line
            WHERE partial_reconcile_id IS NOT NULL
        """
        )
        existing_partial_ids = [r[0] for r in self.env.cr.fetchall()]
        # Search only unprocessed partials directly in the domain
        partials = self.env["account.partial.reconcile"].search(
            [("id", "not in", existing_partial_ids)]
        )
        vals_list = []
        for partial in partials:
            new_vals = self._process_partial_reconcile(partial)
            vals_list.extend(new_vals)
        if vals_list:
            self._strip_internal_keys(vals_list)
            self.sudo().create(vals_list)
            _logger.info(
                "Cash basis: created %d reconciliation lines from %d " "partials.",
                len(vals_list),
                len(partials),
            )

    @api.model
    def _process_partial_reconcile(self, partial):
        """Process a single partial reconcile and return vals list."""
        debit_line = partial.debit_move_id
        credit_line = partial.credit_move_id
        debit_move = debit_line.move_id
        credit_move = credit_line.move_id
        # Only process posted moves
        if debit_move.state != "posted" or credit_move.state != "posted":
            return []
        is_payable_recon = debit_line.account_id.internal_type in (
            "receivable",
            "payable",
        )
        debit_is_cash = debit_move.journal_id.type in CASH_BASIS_JOURNAL_TYPES
        credit_is_cash = credit_move.journal_id.type in CASH_BASIS_JOURNAL_TYPES
        # If both are cash basis journals, skip (handled by Source 1)
        if debit_is_cash and credit_is_cash:
            return []
        vals_list = []
        moves_to_process = self.env["account.move"]
        if is_payable_recon:
            # Payable reconciliation (e.g. payment vs invoice):
            # process the non-cash-basis side
            if not debit_is_cash:
                moves_to_process |= debit_move
            if not credit_is_cash:
                moves_to_process |= credit_move
        else:
            # Non-payable reconciliation (e.g. advance clearing):
            # only process moves WITHOUT payable/receivable lines,
            # as the other side was already recognized via payable recon.
            for move in (debit_move, credit_move):
                if move.journal_id.type in CASH_BASIS_JOURNAL_TYPES:
                    continue
                has_payable = any(
                    line.account_id.internal_type in ("receivable", "payable")
                    for line in move.line_ids
                )
                if not has_payable:
                    moves_to_process |= move
        for move in moves_to_process:
            # Calculate percentage based on partial amount vs
            # receivable/payable total (not sum of all debits/credits).
            # This correctly handles deposit offsets where sum of debits
            # differs from the actual payable/receivable amount.
            move_total = self._get_reconcilable_total(move)
            if not move_total:
                continue
            percentage = (partial.amount / move_total) * 100.0
            move_vals = []
            for line in move.line_ids:
                move_vals.append(
                    self._prepare_cash_basis_line_vals(
                        line,
                        partial.max_date,
                        partial=partial,
                        percentage=percentage,
                    )
                )
            self._adjust_rounding_difference(
                move_vals, move, partial_amount=partial.amount
            )
            vals_list.extend(move_vals)
        return vals_list

    @api.model
    def _strip_internal_keys(self, vals_list):
        """Remove internal keys (prefixed with _) before ORM create."""
        for vals in vals_list:
            for key in list(vals):
                if key.startswith("_"):
                    del vals[key]

    @api.model
    def _get_reconcilable_total(self, move):
        """Get the receivable/payable total for percentage calculation.

        Use the reconcilable (receivable/payable) line amount instead of
        sum of all debits, so that deposit offsets and other contra lines
        do not inflate the denominator.
        """
        reconcilable_lines = move.line_ids.filtered(
            lambda line: line.account_id.internal_type in ("receivable", "payable")
        )
        if reconcilable_lines:
            return abs(sum(reconcilable_lines.mapped("balance")))
        # Fallback for moves without receivable/payable lines
        total = sum(move.line_ids.mapped("debit"))
        if not total:
            total = sum(move.line_ids.mapped("credit"))
        return total

    @api.model
    def _adjust_rounding_difference(self, vals_list, move, partial_amount=0.0):
        """Adjust rounding to ensure total debit == total credit.

        When partial_amount is provided (from reconciliation), first fix
        payable/receivable lines to match partial_amount exactly, then
        adjust the largest non-payable line for overall balance.
        """
        if not vals_list:
            return
        prec = move.company_id.currency_id.rounding
        # Step 1: Fix payable/receivable total to match partial_amount
        if partial_amount:
            self._fix_payable_to_partial(vals_list, partial_amount, prec)
        # Step 2: Ensure overall balance (total debit == total credit)
        total_debit = sum(v["debit"] for v in vals_list)
        total_credit = sum(v["credit"] for v in vals_list)
        diff = float_round(total_debit - total_credit, precision_rounding=prec)
        if not diff:
            return
        # Adjust the largest non-payable line to absorb the difference
        other_lines = [
            v
            for v in vals_list
            if v.get("_account_internal_type") not in ("receivable", "payable")
        ]
        if not other_lines:
            other_lines = vals_list
        if diff > 0:
            target = max(other_lines, key=lambda v: v["debit"])
            target["debit"] = float_round(
                target["debit"] - diff, precision_rounding=prec
            )
        else:
            target = max(other_lines, key=lambda v: v["credit"])
            target["credit"] = float_round(
                target["credit"] + diff, precision_rounding=prec
            )
        target["balance"] = float_round(
            target["debit"] - target["credit"], precision_rounding=prec
        )

    @api.model
    def _fix_payable_to_partial(self, vals_list, partial_amount, prec):
        """Fix payable/receivable lines so their total matches partial_amount.

        This prevents rounding drift when multiple partial reconciles
        each round payable amounts independently.
        """
        payable_vals = [
            v
            for v in vals_list
            if v.get("_account_internal_type") in ("receivable", "payable")
        ]
        if not payable_vals:
            return
        # Payable lines are on credit side for vendor bills,
        # debit side for customer invoices
        payable_debit = sum(v["debit"] for v in payable_vals)
        payable_credit = sum(v["credit"] for v in payable_vals)
        if payable_credit > payable_debit:
            # Vendor bill: payable is on credit side
            diff = float_round(
                payable_credit - payable_debit - partial_amount,
                precision_rounding=prec,
            )
            if diff:
                target = max(payable_vals, key=lambda v: v["credit"])
                target["credit"] = float_round(
                    target["credit"] - diff, precision_rounding=prec
                )
                target["balance"] = float_round(
                    target["debit"] - target["credit"],
                    precision_rounding=prec,
                )
        elif payable_debit > payable_credit:
            # Customer invoice/refund: payable is on debit side
            diff = float_round(
                payable_debit - payable_credit - partial_amount,
                precision_rounding=prec,
            )
            if diff:
                target = max(payable_vals, key=lambda v: v["debit"])
                target["debit"] = float_round(
                    target["debit"] - diff, precision_rounding=prec
                )
                target["balance"] = float_round(
                    target["debit"] - target["credit"],
                    precision_rounding=prec,
                )
