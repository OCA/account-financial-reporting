# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models


class CustomerOutstandingStatement(models.AbstractModel):
    """Model of Customer Outstanding Statement"""

    _inherit = 'report.statement.common'
    _name = 'report.customer_outstanding_statement.statement'

    def _display_lines_sql_q0(self, date_end):
        return self._cr.mogrify("""
            SELECT l1.id,
            CASE WHEN l1.reconciled = TRUE and l1.balance > 0.0
                                THEN max(pd.max_date)
                WHEN l1.reconciled = TRUE and l1.balance < 0.0
                                THEN max(pc.max_date)
                ELSE null
            END as reconciled_date
            FROM account_move_line l1
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.credit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pd ON pd.debit_move_id = l1.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.debit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pc ON pc.credit_move_id = l1.id
            GROUP BY l1.id
        """, locals()
        )

    def _display_lines_sql_q1(self, partners, date_end, account_type):
        partners = tuple(partners)
        return self._cr.mogrify("""
            SELECT m.name AS move_id, l.partner_id, l.date, l.name,
                            l.ref, l.blocked, l.currency_id, l.company_id,
            CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                THEN avg(l.amount_currency)
                ELSE avg(l.debit)
            END as debit,
            CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                THEN avg(l.amount_currency * (-1))
                ELSE avg(l.credit)
            END as credit,
            CASE WHEN l.balance > 0.0
                THEN l.balance - sum(coalesce(pd.amount, 0.0))
                ELSE l.balance + sum(coalesce(pc.amount, 0.0))
            END AS open_amount,
            CASE WHEN l.balance > 0.0
                THEN l.amount_currency - sum(coalesce(pd.amount_currency, 0.0))
                ELSE l.amount_currency + sum(coalesce(pc.amount_currency, 0.0))
            END AS open_amount_currency,
            CASE WHEN l.date_maturity is null
                THEN l.date
                ELSE l.date_maturity
            END as date_maturity
            FROM account_move_line l
            JOIN account_account_type at ON (at.id = l.user_type_id)
            JOIN account_move m ON (l.move_id = m.id)
            LEFT JOIN Q0 ON Q0.id = l.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.credit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pd ON pd.debit_move_id = l.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.debit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pc ON pc.credit_move_id = l.id
            WHERE l.partner_id IN %(partners)s AND at.type = %(account_type)s
                                AND (Q0.reconciled_date is null or
                                    Q0.reconciled_date > %(date_end)s)
                                AND l.date <= %(date_end)s
            GROUP BY l.partner_id, m.name, l.date, l.date_maturity, l.name,
                                l.ref, l.blocked, l.currency_id,
                                l.balance, l.amount_currency, l.company_id
        """, locals())

    def _display_lines_sql_q2(self):
        return self._cr.mogrify("""
            SELECT partner_id, currency_id, move_id, date, date_maturity,
                            debit, credit, name, ref, blocked, company_id,
            CASE WHEN currency_id is not null
                    THEN open_amount_currency
                    ELSE open_amount
            END as open_amount
            FROM Q1
        """, locals())

    def _display_lines_sql_q3(self, company_id):
        return self._cr.mogrify("""
            SELECT Q2.partner_id, move_id, date, date_maturity, Q2.name, ref,
                            debit, credit, debit-credit AS amount, blocked,
            COALESCE(Q2.currency_id, c.currency_id) AS currency_id, open_amount
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            WHERE c.id = %(company_id)s
        """, locals())

    def _get_account_display_lines(self, company_id, partner_ids, date_end,
                                   account_type):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)
        # pylint: disable=E8103
        self.env.cr.execute("""
        WITH Q0 as (%s),
             Q1 AS (%s),
             Q2 AS (%s),
             Q3 AS (%s)
        SELECT partner_id, currency_id, move_id, date, date_maturity, debit,
                            credit, amount, open_amount, name, ref, blocked
        FROM Q3
        ORDER BY date, date_maturity, move_id""" % (
            self._display_lines_sql_q0(date_end),
            self._display_lines_sql_q1(partners, date_end, account_type),
            self._display_lines_sql_q2(),
            self._display_lines_sql_q3(company_id)))
        for row in self.env.cr.dictfetchall():
            res[row.pop('partner_id')].append(row)
        return res

    @api.multi
    def get_report_values(self, docids, data):
        company_id = data['company_id']
        partner_ids = data['partner_ids']
        date_end = data['date_end']
        account_type = data['account_type']
        today = fields.Date.today()

        buckets_to_display = {}
        lines_to_display, amount_due = {}, {}
        currency_to_display = {}
        today_display, date_end_display = {}, {}

        lines = self._get_account_display_lines(
            company_id, partner_ids, date_end, account_type)

        for partner_id in partner_ids:
            lines_to_display[partner_id], amount_due[partner_id] = {}, {}
            currency_to_display[partner_id] = {}
            today_display[partner_id] = self._format_date_to_partner_lang(
                today, partner_id)
            date_end_display[partner_id] = self._format_date_to_partner_lang(
                date_end, partner_id)
            for line in lines[partner_id]:
                currency = self.env['res.currency'].browse(line['currency_id'])
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    currency_to_display[partner_id][currency] = currency
                    amount_due[partner_id][currency] = 0.0
                if not line['blocked']:
                    amount_due[partner_id][currency] += line['open_amount']
                line['balance'] = amount_due[partner_id][currency]
                line['date'] = self._format_date_to_partner_lang(
                    line['date'], partner_id)
                line['date_maturity'] = self._format_date_to_partner_lang(
                    line['date_maturity'], partner_id)
                lines_to_display[partner_id][currency].append(line)

        if data['show_aging_buckets']:
            buckets_to_display = self._get_account_show_buckets(
                company_id, partner_ids, date_end, account_type)

        return {
            'doc_ids': partner_ids,
            'doc_model': 'res.partner',
            'docs': self.env['res.partner'].browse(partner_ids),
            'Amount_Due': amount_due,
            'Lines': lines_to_display,
            'Buckets': buckets_to_display,
            'Currencies': currency_to_display,
            'Show_Buckets': data['show_aging_buckets'],
            'Filter_non_due_partners': data['filter_non_due_partners'],
            'Date_end': date_end_display,
            'Date': today_display,
            'account_type': account_type,
        }
