# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import time
from odoo import api, models, _


class SummaryReport(models.AbstractModel):
    _name = 'report.bank_statement_reconciliation_summary.summary_report'

    @api.model
    def _plus_outstanding_payments(self, journals, end_date):
        rec = {}
        for journal in journals:
            account_id = journal.default_debit_account_id.id
            account_move_line_records = self.env['account.move.line'].search([
                ('account_id', '=', account_id),
                ('reconciled', '=', False),
                ('account_id.reconcile', '=', False),
                ('credit', '>', 0.00),
                ('date', '<=', end_date),
            ], order='date')
            rec[journal.id] = account_move_line_records
        return rec

    @api.model
    def _less_outstanding_receipts(self, journals, end_date):
        rec = {}
        for journal in journals:
            account_id = journal.default_debit_account_id.id
            account_move_line_records = self.env['account.move.line'].search([
                ('account_id', '=', account_id),
                ('reconciled', '=', False),
                ('account_id.reconcile', '=', False),
                ('debit', '>', 0.00),
                ('date', '<=', end_date),
            ], order='date')
            rec[journal.id] = account_move_line_records
        return rec

    @api.model
    def _plus_unreconciled_statement_lines(self, journals, end_date):
        rec = {}
        for journal in journals:
            statement_lines = self.env['account.bank.statement.line'].search(
                [('date', '<=', end_date),
                 ('journal_id', '=', journal.id)])
            for line in statement_lines:
                if not line.journal_entry_ids:
                    statement_lines += line
            rec[journal.id] = statement_lines or False
        return rec

    @api.model
    def _get_bank_end_balance(self, journals, end_date):
        rec = {}
        for journal in journals:
            bank_account = journal.default_credit_account_id
            amount_field = 'balance'
            query = """
            SELECT sum(%s) FROM account_move_line
            WHERE account_id=%%s 
            AND date<=%%s""" % (amount_field,)
            self.env.cr.execute(query, (bank_account.id, end_date))
            query_results = self.env.cr.dictfetchall()
            if query_results:
                account_bal = query_results[0].get('sum') or 0.0
            else:
                account_bal = 0.0
            rec[journal.id] = account_bal
        return rec

    @api.multi
    def render_html(self, docids, data=None):
        Report = self.env['report']
        report_name = 'bank_statement_reconciliation_summary.summary_report'
        report = Report._get_report_from_name(report_name)
        records = self.env['account.journal'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'docs': records,
            'time': time,
            'plus_outstanding_payments':
                self._plus_outstanding_payments(records, data['end_date']),
            'less_outstanding_receipts':
                self._less_outstanding_receipts(records, data['end_date']),
            'plus_unreconciled_statement_lines':
                self._plus_unreconciled_statement_lines(records,
                                                        data['end_date']),
            'bank_end_balance': self._get_bank_end_balance(
                records, data['end_date']),
            'balance_end_real': data['balance_end_real']
        }
        return self.env['report'].render(report_name, docargs)
