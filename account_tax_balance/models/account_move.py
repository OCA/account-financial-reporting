# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _selection_financial_type(self):
        return [
            ("other", self.env._("Other")),
            ("liquidity", self.env._("Liquidity")),
            ("receivable", self.env._("Receivable")),
            ("receivable_refund", self.env._("Receivable refund")),
            ("payable", self.env._("Payable")),
            ("payable_refund", self.env._("Payable refund")),
        ]

    financial_type = fields.Selection(
        selection="_selection_financial_type",
        compute="_compute_financial_type",
        store=True,
        readonly=True,
    )

    @api.depends("line_ids.account_id.account_type", "line_ids.balance")
    def _compute_financial_type(self):
        def _balance_get(line_ids, account_type):
            return sum(
                line_ids.filtered(
                    lambda x: x.account_id.account_type == account_type
                ).mapped("balance")
            )

        for move in self:
            account_types = move.line_ids.mapped("account_id.account_type")
            if (
                "asset_cash" in account_types
                or "liability_credit_card" in account_types
            ):
                move.financial_type = "liquidity"
            elif "liability_payable" in account_types:
                balance = _balance_get(move.line_ids, "liability_payable")
                move.financial_type = "payable" if balance < 0 else "payable_refund"
            elif "asset_receivable" in account_types:
                balance = _balance_get(move.line_ids, "asset_receivable")
                move.financial_type = (
                    "receivable" if balance > 0 else "receivable_refund"
                )
            else:
                move.financial_type = "other"
