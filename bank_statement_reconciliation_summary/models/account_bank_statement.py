# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    @api.multi
    def delete_unreconciled(self):
        self.ensure_one()
        for line in self.line_ids:
            if not line.journal_entry_id:
                line.unlink()


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    clearing_move_line_id = fields.Many2one('account.move.line',
                                            'Clearing Move Line')
