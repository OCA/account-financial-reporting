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

import itertools

from openerp import pooler
from openerp.report import report_sxw
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

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
            'get_current_invoice_lines': self._get_current_invoice_lines,
            'get_balance': self._get_balance,
        })
        self.partner_invoices_dict = {}
        self.ttype = 'receipt'

    def _get_balance(self, partner, company, date=False):
        """
        Get the lines of balance to display in the report
        """
        today = date and datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) \
            or datetime.now()
        date_30 = today - relativedelta(days=30)
        date_60 = today - relativedelta(days=60)
        date_90 = today - relativedelta(days=90)
        date_120 = today - relativedelta(days=120)

        today = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_30 = date_30.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_60 = date_60.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_90 = date_90.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date_120 = date_120.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = sorted(movelines, key=lambda x: x['currency_name'])

        grouped_movelines = [
            (key, list(group)) for key, group in itertools.groupby(
                movelines, key=lambda x: x['currency_name'])
        ]

        res = {}
        for currency_name, lines in grouped_movelines:
            res[currency_name] = {
                'not_due': 0,
                '30': 0,
                '3060': 0,
                '6090': 0,
                '90120': 0,
                '120': 0,
                'total': 0,
                'currency_name': currency_name,
            }
            current_dict = res[currency_name]

            for line in lines:
                amount = line['amount_unreconciled']

                if line['date_due'] > today or not line['date_due']:
                    current_dict['not_due'] += amount

                elif line['date_due'] > date_30:
                    current_dict['30'] += amount

                elif line['date_due'] > date_60:
                    current_dict['3060'] += amount

                elif line['date_due'] > date_90:
                    current_dict['6090'] += amount

                elif line['date_due'] > date_120:
                    current_dict['90120'] += amount

                elif line['date_due']:
                    current_dict['120'] += amount

                current_dict['total'] += amount

        return res.values()

    def _get_current_invoice_lines(self, partner, company, date):
        """
        Get all invoices with unpaid amounts for the given supplier
        :return: a list of dict containing invoice data
        {
            'date_due': the date of maturity
            'amount_original': the original date
            'amount_unreconciled': the amount left to pay
            'currency_id': the currency of the move line
            'currency_name': the name of the currency
            'name': the name of the move line
        }
        """
        # Only compute this method one time per partner
        if partner.id in self.partner_invoices_dict:
            return self.partner_invoices_dict[partner.id]

        voucher_obj = pooler.get_pool(self.cr.dbname)['account.voucher']
        journal_obj = pooler.get_pool(self.cr.dbname)['account.journal']
        move_line_obj = pooler.get_pool(self.cr.dbname)['account.move.line']
        currency_obj = pooler.get_pool(self.cr.dbname)['res.currency']

        currency = company.currency_id

        # Get the journal with the correct currency
        journal_ids = journal_obj.search(
            self.cr, self.uid, [
                ('type', 'in', ['bank', 'cash']),
                ('currency', '=', currency.id),
            ], context=self.localcontext)

        if not journal_ids:
            journal_ids = journal_obj.search(
                self.cr, self.uid, [('type', 'in', ['bank', 'cash'])],
                context=self.localcontext)

        journal_id = journal_ids[0]

        # Retreive every invoice in a first time
        voucher_lines = voucher_obj.recompute_voucher_lines(
            self.cr, self.uid, ids=False, partner_id=partner.id,
            journal_id=journal_id, price=0, currency_id=currency.id,
            ttype=self.ttype, date=date, context=self.localcontext)['value']

        # Map the result by move line
        line_dict = {
            line['move_line_id']: line for line in
            voucher_lines['line_cr_ids'] + voucher_lines['line_dr_ids']
        }

        # If some of the invoices have different currency than the currency
        # of the company, need to get the lines in these currency
        other_currencies = {}
        for move_line in move_line_obj.browse(
            self.cr, self.uid, line_dict.keys(), context=self.localcontext
        ):
            invoice = move_line.invoice
            if invoice and invoice.currency_id.id != currency.id:
                if invoice.currency_id.id in other_currencies:
                    other_currencies[invoice.currency_id.id]['move_line_ids'].\
                        append(invoice.id)
                else:
                    # Get the journal with the correct currency
                    journal_ids = journal_obj.search(
                        self.cr, self.uid, [
                            ('type', 'in', ['bank', 'cash']),
                            ('currency', '=', invoice.currency_id.id),
                        ], context=self.localcontext)

                    if not journal_ids:
                        journal_ids = journal_obj.search(
                            self.cr, self.uid,
                            [('type', 'in', ['bank', 'cash'])],
                            context=self.localcontext)

                    journal_id = journal_ids[0]

                    lines_in_currency = voucher_obj.recompute_voucher_lines(
                        self.cr, self.uid, ids=False, partner_id=partner.id,
                        journal_id=journal_id, price=0,
                        currency_id=invoice.currency_id.id,
                        ttype=self.ttype, date=date,
                        context=self.localcontext)['value']

                    other_currencies[invoice.currency_id.id] = {
                        'lines_in_currency': {
                            line['move_line_id']: line for line in
                            lines_in_currency['line_cr_ids']
                            + lines_in_currency['line_dr_ids']
                        },
                        'move_line_ids': [move_line.id],
                    }

        for currency_id in other_currencies:
            for move_line_id in other_currencies[currency_id]['move_line_ids']:
                line_dict[move_line_id] = other_currencies[currency_id][
                    'lines_in_currency'][move_line_id]

        for line in line_dict:
            move_line = move_line_obj.browse(
                self.cr, self.uid, line_dict[line]['move_line_id'],
                context=self.localcontext)
            line_dict[line]['ref'] = move_line.ref

            currency = currency_obj.browse(
                self.cr, self.uid, line_dict[line]['currency_id'],
                context=self.localcontext)
            line_dict[line]['currency_name'] = currency.name

        # Adjust the amount signs depending on the report type
        if self.ttype == 'receipt':
            for line in line_dict:
                if line_dict[line]['type'] == 'dr':
                    line_dict[line]['amount_original'] *= -1
                    line_dict[line]['amount_unreconciled'] *= -1

        elif self.ttype == 'payment':
            for line in line_dict:
                if line_dict[line]['type'] == 'cr':
                    line_dict[line]['amount_original'] *= -1
                    line_dict[line]['amount_unreconciled'] *= -1

        self.partner_invoices_dict[partner.id] = line_dict.values()

        return self.partner_invoices_dict[partner.id]

    def _lines_get30(self, partner, company, date=False):
        today = date and datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) \
            or datetime.now()
        stop = today - relativedelta(days=30)

        today = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        stop = stop.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = [
            line for line in movelines
            if not line['date_due'] or stop < line['date_due'] <= today
        ]
        return movelines

    def _lines_get_30_60(self, partner, company, date=False):
        today = date and datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) \
            or datetime.now()
        start = today - relativedelta(days=30)
        stop = start - relativedelta(days=30)

        today = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        start = start.strftime(DEFAULT_SERVER_DATE_FORMAT)
        stop = stop.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = [
            line for line in movelines
            if stop < line['date_due'] <= start
        ]
        return movelines

    def _lines_get60(self, partner, company, date=False):
        today = date and datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT) \
            or datetime.now()
        start = today - relativedelta(days=60)

        today = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        start = start.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = [
            line for line in movelines
            if line['date_due'] and line['date_due'] <= start
        ]
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


report_sxw.report_sxw(
    'report.webkit.partner_aged_statement_report',
    'res.partner',
    ('addons/'
     'account_partner_aged_statement_webkit/'
     'report/'
     'partner_aged_statement.mako'),
    parser=PartnerAgedTrialReport,
)
