# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    move_type = fields.Selection(
        string="Move type", selection=[
            ('other', 'Other'),
            ('liquidity', 'Liquidity'),
            ('receivable', 'Receivable'),
            ('receivable_refund', 'Receivable refund'),
            ('payable', 'Payable'),
            ('payable_refund', 'Payable refund'),
        ], compute='_compute_move_type', store=True, readonly=True)

    @api.multi
    @api.depends('line_ids.account_id.internal_type', 'line_ids.balance')
    def _compute_move_type(self):
        sequence = (
            ("liquidity", lambda balance: "liquidity"),
            ("payable", lambda balance: ('payable' if balance < 0
                                         else 'payable_refund')),
            ("receivable", lambda balance: ('receivable' if balance > 0
                                            else 'receivable_refund')),
            (False, lambda balance: "other"),
        )
        chunked_self = (
            self[i:i + models.PREFETCH_MAX]
            for i in range(0, len(self), models.PREFETCH_MAX)
        )
        for chunk in chunked_self:
            move_ids = set(chunk.ids)
            for internal_type, criteria in sequence:
                if not move_ids:
                    break
                # Find balances of the expected type for this move
                domain = [
                    ("move_id", "in", list(move_ids)),
                ]
                if internal_type:
                    domain += [
                        ("account_id.internal_type", "=", internal_type),
                    ]
                balances = self.env["account.move.line"].read_group(
                    domain=domain,
                    fields=["move_id", "balance"],
                    groupby=["move_id"],
                )
                for balance in balances:
                    move = self.browse(balance["move_id"][0])
                    # Discard the move for next searches
                    move_ids.discard(move.id)
                    # Update its type
                    move.move_type = criteria(balance["balance"])
