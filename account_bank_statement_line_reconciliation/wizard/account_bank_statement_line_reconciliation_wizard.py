# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountBankStatementLineReconciliationWizard(models.TransientModel):
    _name = "account.bank.statement.line.reconciliation.wizard"

    statement_line_ids = fields.Many2many(
        string='Current values',
        comodel_name='account.bank.statement.line',
        compute='_compute_statement_line_ids',
    )
    new_statement_line_id = fields.Many2one(
        string='New value',
        comodel_name='account.bank.statement.line',
    )

    def _account_move_ids(self):
        ids = self._context.get('active_ids')
        account_move_ids = self.env['account.move']
        if ids:
            account_move_ids = account_move_ids.browse(ids)

            journal_ids = account_move_ids.mapped('journal_id')

            if len(account_move_ids) > 1 and len(journal_ids) > 1:
                msg = _("Please only select Journal entries "
                        "that belongs to the same bank journal")
                raise ValidationError(msg)

        return account_move_ids

    def _compute_statement_line_ids(self):
        for record in self:
            account_move_ids = record._account_move_ids()
            record.statement_line_ids = [
                (6, 0, account_move_ids.mapped('statement_line_id').ids),
            ]

    @api.multi
    def set_new_statement_line_value(self):
        account_move_ids = self._account_move_ids()
        account_move_ids.write({
            'statement_line_id': self.new_statement_line_id.id,
        })
        account_move_ids.mapped("line_ids").write({
            'statement_id': self.new_statement_line_id.statement_id.id,
        })
        return {}
