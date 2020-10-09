# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


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
    @api.depends(
        'line_ids.account_id.internal_type', 'line_ids.balance',
        'line_ids.account_id.user_type_id.type', 'line_ids.invoice_id.type'
    )
    def _compute_move_type(self):
        refund_types = ('in_refund', 'out_refund')

        def _is_refund(line_ids, internal_type):
            """Check whether all the lines of type `internal_type`
            come from a refund."""
            line_ids = line_ids.filtered(
                lambda x: x.account_id.internal_type == internal_type)
            line_types = line_ids.mapped('invoice_id.type')
            if len(line_types) == 1:
                res = line_types[0] in refund_types
            else:
                # Lines are linked to invoices of different types,
                # or to no invoice at all.
                # If their summed balance is negative, this is a refund.
                res = sum(line_ids.mapped('balance')) < 0
            return res

        for move in self:
            move_lines = move.line_ids
            internal_types = move_lines.mapped('account_id.internal_type')
            if 'liquidity' in internal_types:
                move.move_type = 'liquidity'
            elif 'payable' in internal_types:
                is_refund = _is_refund(move_lines, 'payable')
                move.move_type = (
                    'payable' if not is_refund else 'payable_refund')
            elif 'receivable' in internal_types:
                is_refund = _is_refund(move_lines, 'receivable')
                move.move_type = (
                    'receivable' if not is_refund else 'receivable_refund')
            else:
                move.move_type = 'other'
