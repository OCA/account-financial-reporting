# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def _selection_move_type(self):
        return [
            ('other', _('Other')),
            ('liquidity', _('Liquidity')),
            ('receivable', _('Receivable')),
            ('receivable_refund', _('Receivable refund')),
            ('payable', _('Payable')),
            ('payable_refund', _('Payable refund')),
        ]

    move_type = fields.Selection(
        selection='_selection_move_type',
        compute='_compute_move_type', store=True, readonly=True)

    @api.multi
    @api.depends(
        'line_ids.account_id.internal_type', 'line_ids.balance',
        'line_ids.account_id.user_type_id.type'
    )
    def _compute_move_type(self):
        def _balance_get(line_ids, internal_type):
            return sum(line_ids.filtered(
                lambda x: x.account_id.internal_type == internal_type).mapped(
                    'balance'))

        for move in self:
            internal_types = move.line_ids.mapped('account_id.internal_type')
            if 'liquidity' in internal_types:
                move.move_type = 'liquidity'
            elif 'payable' in internal_types:
                balance = _balance_get(move.line_ids, 'payable')
                move.move_type = (
                    'payable' if balance < 0 else 'payable_refund')
            elif 'receivable' in internal_types:
                balance = _balance_get(move.line_ids, 'receivable')
                move.move_type = (
                    'receivable' if balance > 0 else 'receivable_refund')
            else:
                move.move_type = 'other'
