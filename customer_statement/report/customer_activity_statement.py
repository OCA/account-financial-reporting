# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models
from collections import defaultdict


class CustomerActivityStatement(models.AbstractModel):
    """Model of Customer Activity Statement"""

    _inherit = 'report.statement.common'
    _name = 'report.customer_activity_statement.statement'

    def _initial_balance_sql_q1(self, partners, date_start, account_type):
        return self._cr.mogrify("""
            SELECT l.partner_id, l.currency_id, l.company_id,
            CASE WHEN l.currency_id is not null AND l.amount_currency > 0.0
                THEN sum(l.amount_currency)
                ELSE sum(l.debit)
            END as debit,
            CASE WHEN l.currency_id is not null AND l.amount_currency < 0.0
                THEN sum(l.amount_currency * (-1))
                ELSE sum(l.credit)
            END as credit
            FROM account_move_line l
            JOIN account_account_type at ON (at.id = l.user_type_id)
            JOIN account_move m ON (l.move_id = m.id)
            WHERE l.partner_id IN %(partners)s AND at.type = %(account_type)s
                                AND l.date < %(date_start)s AND not l.blocked
            GROUP BY l.partner_id, l.currency_id, l.amount_currency,
                                l.company_id
        """, locals())

    def _initial_balance_sql_q2(self, company_id):
        return """
            SELECT Q1.partner_id, debit-credit AS balance,
            COALESCE(Q1.currency_id, c.currency_id) AS currency_id
            FROM Q1
            JOIN res_company c ON (c.id = Q1.company_id)
            WHERE c.id = %s
        """ % company_id

    def _get_account_initial_balance(self, company_id, partner_ids,
                                     date_start, account_type, currencies):
        balance_start = dict(map(lambda x: (x, []), partner_ids))
        balance_start_to_display = defaultdict({})
        partners = tuple(partner_ids)
        # pylint: disable=E8103
        self.env.cr.execute("""WITH Q1 AS (%s), Q2 AS (%s)
        SELECT partner_id, currency_id, balance
        FROM Q2""" % (self._initial_balance_sql_q1(partners, date_start,
                                                   account_type),
                      self._initial_balance_sql_q2(company_id)))
        for row in self.env.cr.dictfetchall():
            balance_start[row.pop('partner_id')].append(row)

        for partner_id, line in balance_start.items():
            currency = currencies.get(
                line['currency_id'],
                self.env['res.currency'].browse(line['currency_id'])
            )
            balance_start_to_display[partner_id][currency] = \
                line['balance']
        return balance_start_to_display

    def _display_lines_sql_q1(self, partners, date_start, date_end,
                              account_type):
        return self._cr.mogrify("""
            SELECT m.name AS move_id, l.partner_id, l.date, l.name,
                                l.ref, l.blocked, l.currency_id, l.company_id,
            CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                THEN sum(l.amount_currency)
                ELSE sum(l.debit)
            END as debit,
            CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                THEN sum(l.amount_currency * (-1))
                ELSE sum(l.credit)
            END as credit,
            CASE WHEN l.date_maturity is null
                THEN l.date
                ELSE l.date_maturity
            END as date_maturity
            FROM account_move_line l
            JOIN account_account_type at ON (at.id = l.user_type_id)
            JOIN account_move m ON (l.move_id = m.id)
            WHERE l.partner_id IN %(partners)s AND at.type = %(account_type)s
                                AND %(date_start)s <= l.date AND l.date <= %(date_end)s
            GROUP BY l.partner_id, m.name, l.date, l.date_maturity, l.name,
                                l.ref, l.blocked, l.currency_id,
                                l.amount_currency, l.company_id
        """, locals())

    def _display_lines_sql_q2(self, company_id):
        return self._cr.mogrify("""
            SELECT Q1.partner_id, move_id, date, date_maturity, Q1.name, ref,
                            debit, credit, debit-credit as amount, blocked,
            COALESCE(Q1.currency_id, c.currency_id) AS currency_id
            FROM Q1
            JOIN res_company c ON (c.id = Q1.company_id)
            WHERE c.id = %(company_id)s
        """, locals())

    def _get_account_display_lines(self, company_id, partner_ids, date_start,
                                   date_end, account_type):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)

        # pylint: disable=E8103
        self.env.cr.execute("""
        WITH Q1 AS (%s),
             Q2 AS (%s)
        SELECT partner_id, move_id, date, date_maturity, name, ref, debit,
                            credit, amount, blocked, currency_id
        FROM Q2
        ORDER BY date, date_maturity, move_id""" % (
            self._display_lines_sql_q1(partners, date_start, date_end,
                                       account_type),
            self._display_lines_sql_q2(company_id)))
        for row in self.env.cr.dictfetchall():
            res[row.pop('partner_id')].append(row)
        return res

    @api.multi
    def get_report_values(self, docids, data):
        if not data:
            wiz = self.env["customer.activity.statement.wizard"].with_context(
                active_ids=docids, model="res.partner"
            )
            data = wiz.create({})._prepare_statement()
        company_id = data['company_id']
        partner_ids = data['partner_ids']
        date_start = data['date_start']
        date_end = data['date_end']
        account_type = data['account_type']
        today = fields.Date.today()

        # There should be relatively few of these, so to speed performance we cache them
        self._cr.execute("""
            SELECT p.id, l.date_format
            FROM res_partner p LEFT JOIN res_lang l ON p.lang=l.id
            WHERE p.id IN %(partner_ids)s""", {"partner_ids": tuple(partner_ids)})
        date_formats = {r[0]: r[1] for r in self._cr.fetchall()}
        currencies = {x.id: x for x in self.env['res.currency'].search([])}


        buckets_to_display = {}
        lines_to_display = defaultdict({})
        amount_due = defaultdict({})
        currency_to_display = defaultdict({})
        today_display, date_start_display, date_end_display = {}, {}, {}

        balance_start_to_display = self._get_account_initial_balance(
            company_id, partner_ids, date_start, account_type, currencies)

        lines = self._get_account_display_lines(
            company_id, partner_ids, date_start, date_end, account_type)

        for partner_id in partner_ids:
            today_display[partner_id] = self._format_date_to_partner_lang(
                today, partner_id, date_formats['partner_id'])
            date_start_display[partner_id] = self._format_date_to_partner_lang(
                date_start, partner_id, date_formats['partner_id'])
            date_end_display[partner_id] = self._format_date_to_partner_lang(
                date_end, partner_id, date_formats['partner_id'])

            for line in lines[partner_id]:
                currency = self.env['res.currency'].browse(line['currency_id'])
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    currency_to_display[partner_id][currency] = currency
                    if currency in balance_start_to_display[partner_id]:
                        amount_due[partner_id][currency] = \
                            balance_start_to_display[partner_id][currency]
                    else:
                        amount_due[partner_id][currency] = 0.0
                if not line['blocked']:
                    amount_due[partner_id][currency] += line['amount']
                line['balance'] = amount_due[partner_id][currency]
                line['date'] = self._format_date_to_partner_lang(
                    line['date'], partner_id, date_formats['partner_id'])
                line['date_maturity'] = self._format_date_to_partner_lang(
                    line['date_maturity'], partner_id, date_formats['partner_id'])
                lines_to_display[partner_id][currency].append(line)

        if data['show_aging_buckets']:
            buckets_to_display = self._get_account_show_buckets(
                company_id, partner_ids, date_end, account_type)

        return {
            'doc_ids': partner_ids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'Amount_Due': amount_due,
            'Balance_forward': balance_start_to_display,
            'Lines': lines_to_display,
            'Buckets': buckets_to_display,
            'Currencies': currency_to_display,
            'Show_Buckets': data['show_aging_buckets'],
            'Filter_non_due_partners': data['filter_non_due_partners'],
            'Date_start': date_start_display,
            'Date_end': date_end_display,
            'Date': today_display,
            'account_type': account_type,
        }
