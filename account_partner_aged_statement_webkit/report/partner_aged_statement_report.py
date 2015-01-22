# -*- encoding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2010 - 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import time

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import pooler
from openerp.report import report_sxw

from openerp.addons.account.report.account_aged_partner_balance import (
    aged_trial_report
)


class PartnerAgedTrialReport(aged_trial_report):
    _partner = None

    def __init__(self, cr, uid, name, context):
        super(PartnerAgedTrialReport, self).__init__(cr, uid, name, context)
        current_user = self.localcontext["user"]
        self._company = current_user.company_id
        if self.localcontext.get("active_model", "") == "res.partner":
            self._partners = self.localcontext["active_ids"]
        self.localcontext.update({
            'message': self._message,
            'getLines30': self._lines_get30,
            'getLines3060': self._lines_get_30_60,
            'getLines60': self._lines_get60,
            'show_message': True,
            'line_amount': self._line_amount,
            'line_paid': self._line_paid,
            'balance_amount': lambda amount: amount,
        })

    def _lines_get30(self, obj):
        today = datetime.now()
        stop = today - relativedelta(days=30)

        moveline_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        movelines = moveline_obj.search(
            self.cr, self.uid,
            [('partner_id', '=', obj.id),
             ('account_id.type', 'in', ['receivable']),
             ('state', '<>', 'draft'), ('reconcile_id', '=', False),
             '|',
             '&', ('date_maturity', '<=', today), ('date_maturity', '>', stop),
             '&', ('date_maturity', '=', False),
             '&', ('date', '<=', today), ('date', '>', stop)],
            context=self.localcontext)
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

    def _lines_get_30_60(self, obj):
        start = datetime.now() - relativedelta(days=30)
        stop = start - relativedelta(days=30)

        moveline_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        movelines = moveline_obj.search(
            self.cr, self.uid,
            [('partner_id', '=', obj.id),
             ('account_id.type', 'in', ['receivable']),
             ('state', '<>', 'draft'), ('reconcile_id', '=', False),
             '|',
             '&', ('date_maturity', '<=', start), ('date_maturity', '>', stop),
             '&', ('date_maturity', '=', False),
             '&', ('date', '<=', start), ('date', '>', stop)],
            context=self.localcontext)
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

    def _lines_get60(self, obj):
        start = datetime.now() - relativedelta(days=60)

        moveline_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        movelines = moveline_obj.search(
            self.cr, self.uid,
            [('partner_id', '=', obj.id),
             ('account_id.type', 'in', ['receivable']),
             ('state', '<>', 'draft'), ('reconcile_id', '=', False),
             '|', ('date_maturity', '<=', start),
             ('date_maturity', '=', False), ('date', '<=', start)],
            context=self.localcontext)
        movelines = moveline_obj.browse(self.cr, self.uid, movelines)
        return movelines

    def _message(self, obj, company):
        company_pool = pooler.get_pool(self.cr.dbname)['res.company']
        message = company_pool.browse(
            self.cr, self.uid, company.id, {'lang': obj.lang}).overdue_msg
        return message.split('\n')

    def _get_fiscalyear(self, data):
        now = data['fInvoicesorm']['date_from']
        domain = [
            ('company_id', '=', self._company.id),
            ('date_start', '<', now),
            ('date_stop', '>', now),
        ]
        fiscalyears_obj = pooler.get_pool(self.cr.dbname)['account.fiscalyear']
        fiscalyears = fiscalyears_obj.search(
            self.cr, self.uid, domain, limit=1, context=self.localcontext)
        if fiscalyears:
            return fiscalyears_obj.browse(
                self.cr, self.uid, fiscalyears[0], context=self.localcontext
            ).name
        else:
            return ''

    def _get_account(self, data):
        account_obj = pooler.get_pool(self.cr.dbname).get('account.account')
        accounts = account_obj.search(
            self.cr, self.uid,
            [('parent_id', '=', False), ('company_id', '=', self._company.id)],
            limit=1, context=self.localcontext)
        if accounts:
            return account_obj.browse(
                self.cr, self.uid, accounts[0],
                context=self.localcontext).name
        else:
            return ''

    def _get_company(self, data):
        return self._company.name

    def _get_journal(self, data):
        codes = []
        if data.get('form', False) and data['form'].get('journal_ids', False):
            self.cr.execute(
                'select code from account_journal where id IN %s',
                (tuple(data['form']['journal_ids']),)
            )
            codes = [x for x, in self.cr.fetchall()]
        return codes

    def _get_currency(self, data):
        return self._company.currency_id.symbol

    def set_context(self, objects, data, ids, report_type=None):
        period_length = 30
        form = {
            "direction_selection": "past",
            "period_length": period_length,
            "result_selection": "customer",
            "date_from": time.strftime("%Y-%m-%d"),
        }
        # Taken from 'account/wizard/account_report_aged_partner_balance.py
        # which sets data from the form
        start = datetime.now()
        for i in range(4, -1, -1):
            stop = start - relativedelta(days=period_length)
            form[str(i)] = {
                'name': (i != 0 and "{0}-{1}".format(
                    5 - (i + 1), (5 - i) * period_length,
                ) or '+{0}'.format(4 * period_length)),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)

        data["form"] = form
        res = super(PartnerAgedTrialReport, self).set_context(
            objects, data, ids, report_type=report_type)
        self.orig_query = self.query
        if self._partner is not None:
            self.query = "{0} AND l.partner_id = {1}".format(
                self.query,
                ", ".join(str(int(i)) for i in self._partners),
            )

        self.ACCOUNT_TYPE = ['receivable']
        return res

    def _get_lines(self, form, partner):
        # self.query is used to get the lines in super()._get_lines
        self.query = "{0} AND l.partner_id = {1}".format(
            self.orig_query,
            partner.id,)
        res = super(PartnerAgedTrialReport, self)._get_lines(form)
        self.query = self.orig_query
        return res

    def _line_amount(self, line):
        invoice = line.invoice
        invoice_type = invoice and invoice.type or False
        print invoice_type, line.debit, line.account_id.type

        if invoice_type == 'in_invoice':
            return line.credit or 0.0

        if invoice_type == 'in_refund':
            return -line.debit or 0.0

        if invoice_type == 'out_invoice':
            return line.debit or 0.0

        if invoice_type == 'out_refund':
            return -line.credit or 0.0

        if line.account_id.type == 'payable':
            return line.credit or 0.0

        return line.debit or 0.0

    def _line_paid(self, line):
        invoice = line.invoice
        invoice_type = invoice and invoice.type or False

        if invoice_type == 'in_invoice':
            return line.debit or 0.0

        if invoice_type == 'in_refund':
            return -line.credit or 0.0

        if invoice_type == 'out_invoice':
            return line.credit or 0.0

        if invoice_type == 'out_refund':
            return -line.debit or 0.0

        if line.account_id.type == 'payable':
            return line.debit or 0.0

        return line.credit or 0.0


report_sxw.report_sxw(
    'report.webkit.partner_aged_statement_report',
    'res.partner',
    ('addons/'
     'account_partner_aged_statement_webkit/'
     'report/'
     'partner_aged_statement.mako'),
    parser=PartnerAgedTrialReport,
)
