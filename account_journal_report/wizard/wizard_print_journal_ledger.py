# -*- coding: utf-8 -*-
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2017 RGB Consulting
# Copyright 2017 Eficent - Miquel Raich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from openerp import api, fields, models, exceptions, _


class AccountJournalLedgerReport(models.TransientModel):
    _name = "account.journal.entries.report"
    _description = "Print Journal Ledger"

    @api.model
    def _default_journal_ids(self):
        return self.env['account.journal'].search([])

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation="account_journal_entries_report_journals_rel",
        string='Journals', required=True, default=_default_journal_ids,
    )
    date_start = fields.Date(required=True,
                             default=fields.Date.to_string(
                                 date.today()-timedelta(days=90)))
    date_end = fields.Date(required=True,
                           default=fields.Date.to_string(date.today()))
    sort_selection = fields.Selection(
        [('date', 'By date'),
         ('name', 'By entry number'),
         ('ref', 'By reference number')],
        string='Entries Sorted By', required=True, default='name',
    )
    landscape = fields.Boolean(string='Landscape mode', default=True)

    @api.multi
    def _check_data(self):
        if not self.journal_ids:
            return False
        journal_obj = self.env['account.journal']
        for journal in self.journal_ids:
            ids_journal = journal_obj.search(
                [('id', '=', journal.id)])
            if ids_journal:
                return True
        return False

    @api.multi
    def print_report(self):
        """Print report PDF"""

        # Check data
        if not self._check_data():
            raise exceptions.Warning(
                _('No data available'),
                _('No records found for your selection!'))

        report_name = 'account_journal_report.journal_ledger'

        # Call report
        data = self.read()[0]
        return self.env['report'].with_context(
            {'landscape': self.landscape}).get_action(self,
                                                      report_name=report_name,
                                                      data=data)

    @api.multi
    def print_report_xlsx(self):
        """Print report XLSX"""

        # Check data
        if not self._check_data():
            raise exceptions.Warning(
                _('No data available'),
                _('No records found for your selection!'))

        # Call report
        data = self.read()[0]
        report_name = 'account_journal_report.journal_ledger_xlsx'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'report_type': 'xlsx',
            'datas': data}
