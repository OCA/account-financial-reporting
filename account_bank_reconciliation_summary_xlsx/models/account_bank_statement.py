# -*- coding: utf-8 -*-
# © 2017 Akretion France (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def print_reconciliation_xlsx(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.report.xml',
            'report_name': 'bank.reconciliation.xlsx',
            'datas': {
                'model': 'account.journal',
                'ids': [self.journal_id.id],
                },
            'context': self._context,
            }
        return action
