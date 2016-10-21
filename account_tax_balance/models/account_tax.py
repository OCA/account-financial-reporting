# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp.tools.safe_eval import safe_eval


class AccountTax(models.Model):
    _inherit = 'account.tax'

    balance = fields.Float(
        string="Total Balance", compute="_compute_balance",
        search='_search_balance')
    base_balance = fields.Float(
        string="Total Base Balance", compute="_compute_balance",
        search='_search_base_balance')
    balance_regular = fields.Float(
        string="Balance", compute="_compute_balance",
        search='_search_balance_regular')
    base_balance_regular = fields.Float(
        string="Base Balance", compute="_compute_balance",
        search='_search_base_balance_regular')
    balance_refund = fields.Float(
        string="Balance Refund", compute="_compute_balance",
        search='_search_balance_refund')
    base_balance_refund = fields.Float(
        string="Base Balance Refund", compute="_compute_balance",
        search='_search_base_balance_refund')

    def _search_balance_field(self, field, operator, value):
        operators = {'>', '<', '>=', '<=', '!=', '=', '<>'}
        fields = {
            'balance', 'base_balance', 'balance_regular',
            'base_balance_regular', 'balance_refund', 'base_balance_refund',
        }
        domain = []
        if operator in operators and field in fields:
            value = float(value) if value else 0
            taxes = self.search([]).filtered(
                lambda x: safe_eval(
                    '%.2f %s %.2f' % (x[field], operator, value)))
            domain.append(('id', 'in', taxes.ids))
        return domain

    def _search_balance(self, operator, value):
        return self._search_balance_field('balance', operator, value)

    def _search_base_balance(self, operator, value):
        return self._search_balance_field('base_balance', operator, value)

    def _search_balance_regular(self, operator, value):
        return self._search_balance_field('balance_regular', operator, value)

    def _search_base_balance_regular(self, operator, value):
        return self._search_balance_field(
            'base_balance_regular', operator, value)

    def _search_balance_refund(self, operator, value):
        return self._search_balance_field('balance_refund', operator, value)

    def _search_base_balance_refund(self, operator, value):
        return self._search_balance_field(
            'base_balance_refund', operator, value)

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
            tax.balance_regular = tax.compute_balance(
                tax_or_base='tax', move_type='regular')
            tax.base_balance_regular = tax.compute_balance(
                tax_or_base='base', move_type='regular')
            tax.balance_refund = tax.compute_balance(
                tax_or_base='tax', move_type='refund')
            tax.base_balance_refund = tax.compute_balance(
                tax_or_base='base', move_type='refund')
            tax.balance = tax.balance_regular + tax.balance_refund
            tax.base_balance = (
                tax.base_balance_regular + tax.base_balance_refund)

    def get_target_type_list(self, move_type=None):
        if move_type == 'refund':
            return ['receivable_refund', 'payable_refund']
        elif move_type == 'regular':
            return ['receivable', 'payable']
        return []

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

    def compute_balance(self, tax_or_base='tax', move_type=None):
        self.ensure_one()
        move_lines = self.get_move_lines_domain(
            tax_or_base=tax_or_base, move_type=move_type)
        # balance is debit - credit whereas on tax return you want to see what
        # vat has to be paid so:
        # VAT on sales (credit) - VAT on purchases (debit).
        total = -sum([l.balance for l in move_lines])
        return total

    def get_balance_domain(self, state_list, type_list):
        domain = [
            ('move_id.state', 'in', state_list),
            ('tax_line_id', '=', self.id),
        ]
        if type_list:
            domain.append(('move_id.move_type', 'in', type_list))
        return domain

    def get_base_balance_domain(self, state_list, type_list):
        domain = [
            ('move_id.state', 'in', state_list),
            ('tax_ids', 'in', self.id),
        ]
        if type_list:
            domain.append(('move_id.move_type', 'in', type_list))
        return domain

    def get_move_lines_domain(self, tax_or_base='tax', move_type=None):
        move_line_model = self.env['account.move.line']
        from_date, to_date, company_id, target_move = self.get_context_values()
        state_list = self.get_target_state_list(target_move)
        type_list = self.get_target_type_list(move_type)
        domain = self.get_move_line_partial_domain(
            from_date, to_date, company_id)
        balance_domain = []
        if tax_or_base == 'tax':
            balance_domain = self.get_balance_domain(state_list, type_list)
        elif tax_or_base == 'base':
            balance_domain = self.get_base_balance_domain(
                state_list, type_list)
        domain.extend(balance_domain)
        return move_line_model.search(domain)

    def get_lines_action(self, tax_or_base='tax', move_type=None):
        move_lines = self.get_move_lines_domain(
            tax_or_base=tax_or_base, move_type=move_type)
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

    @api.multi
    def view_tax_regular_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax', move_type='regular')

    @api.multi
    def view_base_regular_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base', move_type='regular')

    @api.multi
    def view_tax_refund_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax', move_type='refund')

    @api.multi
    def view_base_refund_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base', move_type='refund')
