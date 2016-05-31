# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
from openerp.tools import misc
from openerp.exceptions import Warning
from openerp.tools.translate import _


class SummaryReport(models.TransientModel):
    _name = 'wiz.bank.unreconcile'

    @api.model
    def _get_unreconcile_entries(self):
        cr, uid, context = self.env.args
        context = dict(context)
        statement_line_obj = self.env['account.bank.statement.line']
        move_line_obj = self.env['account.move.line']
        bank_id = context.get('active_id')
        self.env.args = cr, uid, misc.frozendict(context)
        bank = self.env['account.bank.statement'].browse(bank_id)
        clearing_account_id = bank.journal_id and\
            bank.journal_id.default_credit_account_id and\
            bank.journal_id.default_credit_account_id.clearing_account_id and\
            bank.journal_id.default_credit_account_id.clearing_account_id.id
        if clearing_account_id:
            to_add_move_lines = move_line_obj.browse()
            account_move_line_records = self.env['account.move.line'].search([
                ('account_id', '=', clearing_account_id),
                ('account_id.reconcile', '=', True),
                '|',
                ('reconcile_id', '=', False),
                ('reconcile_partial_id', '!=', False)
            ], order='date')
            statements = statement_line_obj.search(
                [('statement_id', '=', bank_id),
                 ('clearing_move_line_id', 'in',
                  account_move_line_records.ids)])
            in_statement_clearing_lines = []
            for statement in statements:
                in_statement_clearing_lines += \
                    statement.clearing_move_line_id
            for move_line in account_move_line_records:
                if move_line not in in_statement_clearing_lines:
                    to_add_move_lines += move_line
        else:
            raise Warning(_("Create an Clearing Account to get "
                            "the Unreconciled Journal Items."))
        return to_add_move_lines

    line_ids = fields.Many2many('account.move.line',
                                'wiz_unreconciles_move_line_rel',
                                'reconciles_id', 'accounts_id',
                                'Journal Items to Reconcile',
                                default=_get_unreconcile_entries)

    @api.multi
    def process_wiz(self):
        context = dict(self._context)
        bank_stmt_obj = self.env['account.bank.statement']
        currency_obj = self.env['res.currency']
        statement = bank_stmt_obj.browse(context.get('active_ids'))
        lines = []
        for line in self.line_ids:
            currency_obj = currency_obj.with_context(date=statement.date)
            amount = 0.0
            if line.debit > 0:
                amount = line.debit
            elif line.credit > 0:
                amount = -line.credit
            if line.amount_currency:
                if line.company_id.currency_id.id != statement.currency.id:
                    amount = line.currency_id.with_context(
                        date=statement.date).compute(line.amount_currency,
                                                     statement.currency)
            elif (line.currency_id and
                    line.currency_id.id != statement.currency.id):
                amount = line.currency_id.with_context(
                        date=statement.date).compute(amount,
                                                     statement.currency)
            lines.append((0, 0, {
                'name': line.name or '?',
                'ref': line.ref,
                'partner_id': line.partner_id.id,
                'amount': amount,
                'date': line.date,
                'amount_currency': line.amount_currency,
                'currency_id': line.currency_id.id,
                'clearing_move_line_id': line.id,
            }))
        statement.write({'line_ids': lines})
        return True
