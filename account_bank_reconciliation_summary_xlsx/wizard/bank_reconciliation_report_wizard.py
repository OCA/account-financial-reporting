# -*- coding: utf-8 -*-
# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BankReconciliationReportWizard(models.TransientModel):
    _name = "bank.reconciliation.report.wizard"
    _description = "Bank Reconciliation Report Wizard"

    @api.model
    def _default_journal_ids(self):
        journals = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.user.company_id.id)])
        return journals

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    date = fields.Date(
        required=True,
        default=fields.Date.context_today)
    journal_ids = fields.Many2many(
        'account.journal', string='Bank Journals',
        domain=[('type', '=', 'bank')], required=True,
        default=_default_journal_ids)

    def open_xlsx(self):
        action = {
            'type': 'ir.actions.report.xml',
            'report_name': 'bank.reconciliation.xlsx',
            'datas': {
                'model': 'account.journal',
                'ids': self.journal_ids.ids,
                'date': self.date,
                },
            'context': self._context,
            }
        return action
