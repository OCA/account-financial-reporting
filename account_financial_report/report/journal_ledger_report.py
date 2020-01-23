# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class JournalLedgerReport(models.Model):
    _name = "journal.ledger.report"
    _description = "Journal Ledger Report"
    _auto = False
    _rec_name = 'entry_name'
    _order = 'journal_id,partner_id,date desc'

    journal_id = fields.Many2one('account.journal', readonly=True)
    entry_name = fields.Char('Account Move Entry Name', readonly=True)
    date = fields.Datetime('Entry Date', readonly=True)
    account_id = fields.Many2one('account.account', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    ref_label = fields.Char('Ref - Label', readonly=True)
    taxes_name = fields.Many2one('account.tax', 'Taxes', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(aml.id) as id,
            aml.journal_id as journal_id,
            am.name as entry_name,
            am.date as date,
            aml.account_id as account_id,
            aml.partner_id as partner_id,
            aml.name as ref_label,
            string_agg(at.name, ', ') AS taxes_name,
            aml.debit as debit,
            aml.credit as credit
        """

        for field in fields.values():
            select_ += field

        from_ = """
                account_move_line aml
                      join account_move am on aml.move_id=am.id
                      left join account_move_line_account_tax_rel amlatr on amlatr.account_move_line_id = aml.id
                      left join account_tax at on amlatr.account_tax_id = at.id
                %s
        """ % from_clause

        groupby_ = """
            aml.journal_id,
            aml.account_id,
            aml.partner_id,
            am.name,
            am.date,
            aml.name,
            aml.debit,
            aml.credit
            %s
        """ % (groupby)

        orderby_ = """
        aml.journal_id, aml.partner_id, am.date
        """

        return '%s (SELECT %s FROM %s GROUP BY %s ORDER BY %s)' % (with_, select_, from_, groupby_, orderby_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
