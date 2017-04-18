# -*- coding: utf-8 -*-
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2017 RGB Consulting
# Copyright 2017 Eficent - Miquel Raich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class JournalLedger(models.AbstractModel):
    _name = 'report.account_journal_report.journal_ledger'

    def _format_date_to_lang(self, str_date):
        if 'lang' not in self._context:
            return str_date
        lang_code = self._context['lang']
        lang_id = self.env['res.lang']._lang_get(lang_code)
        lang = self.env['res.lang'].browse(lang_id)
        date = fields.Date.from_string(str_date)
        return date.strftime(lang.date_format)

    @api.multi
    def render_html(self, data):
        account_move_obj = self.env['account.move']
        report_obj = self.env['report']

        date_start = data.get('date_start')
        date_end = data.get('date_end')
        journal_ids = data.get('journal_ids', [])

        move_ids = account_move_obj.search(
            [('date', '<=', date_end),
             ('date', '>=', date_start),
             ('journal_id', 'in', journal_ids),
             ('state', '!=', 'draft')],
            order=data.get('sort_selection', 'date') + ', id')

        report = report_obj._get_report_from_name(
            'account_journal_report.journal_ledger')
        docargs = {
            'doc_model': report.model,
            'docs': move_ids,
            'date_start': self._format_date_to_lang(
                date_start),
            'date_end': self._format_date_to_lang(
                date_end),
        }
        return report_obj.render(
            'account_journal_report.journal_ledger', docargs)
