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
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta

import itertools

from openerp import pooler
from openerp.addons.report_webkit.webkit_report import WebKitParser
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
            'getLinesCurrent': self._lines_get_current,
            'getLines3060': self._lines_get_30_60,
            'getLines60': self._lines_get_60,
            'show_message': True,
            'get_current_invoice_lines': self._get_current_invoice_lines,
            'get_balance': self._get_balance,
        })
        self.partner_invoices_dict = {}
        self.ttype = 'receipt'
        tz = self.localcontext.get('tz', False)
        tz = tz and pytz.timezone(tz) or pytz.utc
        self.today = datetime.now(tz)

    def _get_balance(self, partner, company):
        """
        Get the lines of balance to display in the report
        """
        today = self.today
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
                'current': 0,
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

                if (
                    not line['date_original'] or
                    line['date_original'] >= date_30
                ):
                    current_dict['current'] += amount

                elif line['date_original'] > date_60:
                    current_dict['3060'] += amount

                elif line['date_original'] > date_90:
                    current_dict['6090'] += amount

                elif line['date_original'] > date_120:
                    current_dict['90120'] += amount

                else:
                    current_dict['120'] += amount

                current_dict['total'] += amount

        return res.values()

    def _get_current_invoice_lines(self, partner, company, date):
        """
        Get all invoices with unpaid amounts for the given supplier
        :return: a list of dict containing invoice data
        {
            'date_due': the date of maturity
            'date_original': the date of the invoice
            'ref': the partner reference on the invoice
            'amount_original': the original date
            'amount_unreconciled': the amount left to pay
            'currency_id': the currency of the invoice
            'currency_name': the name of the currency
            'name': the number of the invoice
        }
        """
        # Only compute this method one time per partner
        if partner.id in self.partner_invoices_dict:
            return self.partner_invoices_dict[partner.id]

        pool = pooler.get_pool(self.cr.dbname)
        cr, uid, context = self.cr, self.uid, self.localcontext

        inv_obj = pool['account.invoice']

        invoice_ids = inv_obj.search(cr, uid, [
            ('state', '=', 'open'),
            ('company_id', '=', company.id),
            ('partner_id', '=', partner.id),
            ('type', '=', 'out_invoice'
                if self.ttype == 'receipt' else 'in_invoice'),
        ], context=context)

        invoices = inv_obj.browse(cr, uid, invoice_ids, context=context)

        res = sorted([
            {
                'date_due': inv.date_due or '',
                'date_original': inv.date_invoice or '',
                'amount_original': inv.amount_total,
                'amount_unreconciled': inv.residual,
                'currency_id': inv.currency_id.id,
                'currency_name': inv.currency_id.name,
                'name': inv.number,
                'ref': inv.reference or '',
                'id': inv.id,
            } for inv in invoices
        ], key=lambda inv: inv['date_original'])

        res.reverse()

        return res

    def _lines_get_current(self, partner, company):
        today = self.today
        stop = today - relativedelta(days=30)
        stop = stop.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = [
            line for line in movelines
            if not line['date_original'] or
            line['date_original'] >= stop
        ]
        return movelines

    def _lines_get_30_60(self, partner, company):
        today = self.today
        start = today - relativedelta(days=30)
        stop = start - relativedelta(days=30)

        today = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        start = start.strftime(DEFAULT_SERVER_DATE_FORMAT)
        stop = stop.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = [
            line for line in movelines
            if line['date_original'] and
            stop < line['date_original'] <= start
        ]
        return movelines

    def _lines_get_60(self, partner, company):
        today = self.today
        start = today - relativedelta(days=60)

        today = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        start = start.strftime(DEFAULT_SERVER_DATE_FORMAT)

        movelines = self._get_current_invoice_lines(partner, company, today)
        movelines = [
            line for line in movelines
            if line['date_original'] and
            line['date_original'] <= start
        ]
        return movelines

    def _message(self, obj, company):
        company_pool = pooler.get_pool(self.cr.dbname)['res.company']
        message = company_pool.browse(
            self.cr, self.uid, company.id, {'lang': obj.lang}).overdue_msg
        return message and message.split('\n') or ''

    def _get_company(self, data):
        return self._company.name

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


WebKitParser(
    'report.webkit.partner_aged_statement_report',
    'res.partner',
    ('addons/'
     'account_partner_aged_statement_webkit/'
     'report/'
     'partner_aged_statement.mako'),
    parser=PartnerAgedTrialReport,
)
