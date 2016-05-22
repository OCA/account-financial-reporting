# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    balance = fields.Float(string="Balance", compute="_compute_balance")
    base_balance = fields.Float(
        string="Base Balance", compute="_compute_balance")

    def get_context_values(self):
        context = self.env.context
        return (
            context.get('from_date', fields.Date.context_today(self)),
            context.get('to_date', fields.Date.context_today(self)),
            context.get('company_id', self.env.user.company_id.id),
            context.get('target_move', 'posted')
        )

    def _compute_balance(self):
        for tax in self:
            tax.balance = tax.compute_balance(tax_or_base='tax')
            tax.base_balance = tax.compute_balance(tax_or_base='base')

    def get_target_state_list(self, target_move="posted"):
        if target_move == 'posted':
            state = ['posted']
        elif target_move == 'all':
            state = ['posted', 'draft']
        else:
            state = []
        return state

    def get_move_line_partial_domain(self, from_date, to_date, company_id):
        return [
            ('date', '<=', to_date),
            ('date', '>=', from_date),
            ('company_id', '=', company_id),
        ]

    def compute_balance(self, tax_or_base='tax'):
        self.ensure_one()
        move_lines = self.get_move_lines_domain(tax_or_base=tax_or_base)
        total = sum([l.balance for l in move_lines])
        return total

    def get_balance_domain(self, state_list):
        return [
            ('move_id.state', 'in', state_list),
            ('tax_line_id', '=', self.id),
        ]

    def get_base_balance_domain(self, state_list):
        return [
            ('move_id.state', 'in', state_list),
            ('tax_ids', 'in', self.id),
        ]

    def get_move_lines_domain(self, tax_or_base='tax'):
        move_line_model = self.env['account.move.line']
        from_date, to_date, company_id, target_move = self.get_context_values()
        state_list = self.get_target_state_list(target_move)
        domain = self.get_move_line_partial_domain(
            from_date, to_date, company_id)
        balance_domain = []
        if tax_or_base == 'tax':
            balance_domain = self.get_balance_domain(state_list)
        elif tax_or_base == 'base':
            balance_domain = self.get_base_balance_domain(state_list)
        domain.extend(balance_domain)
        return move_line_model.search(domain)

    def get_lines_action(self, tax_or_base='tax'):
        move_lines = self.get_move_lines_domain(tax_or_base=tax_or_base)
        move_line_ids = [l.id for l in move_lines]
        action = self.env.ref('account.action_account_moves_all_tree')
        vals = action.read()[0]
        vals['context'] = {}
        vals['domain'] = [('id', 'in', move_line_ids)]
        return vals

    @api.multi
    def view_tax_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax')

    @api.multi
    def view_base_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base')
