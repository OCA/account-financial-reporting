# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BankReconciliationReportWizard(models.TransientModel):
    _name = "bank.statement.reconciliation.summary.wizard"
    _description = "Bank Statement Reconciliation Summary Wizard"

    @api.model
    def _default_journal_id(self):
        journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.user.company_id.id)], limit=1)
        return journal

    start_date = fields.Date()
    end_date = fields.Date(
        required=True,
        default=fields.Date.context_today)
    journal_id = fields.Many2one(
        'account.journal', string='Bank Journal',
        domain=[('type', '=', 'bank')], required=True,
        default=_default_journal_id)
    balance_end_real = fields.Float('Bank Ending Balance')

    def open_qweb(self):
        action = {
            'type': 'ir.actions.report.xml',
            'report_name':
                'bank_statement_reconciliation_summary.summary_report',
            'docids': self.journal_id.ids,
            'datas': {
                'docids': self.journal_id.ids,
                'ids': self.journal_id.ids,
                'end_date': self.end_date,
                'start_date': self.start_date,
                'balance_end_real': self.balance_end_real,
                },
            'context': self._context,
            }
        return action
