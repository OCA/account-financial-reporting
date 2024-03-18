# Copyright 2018 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import _, api, models


class ActivityStatement(models.AbstractModel):
    """Model of Activity Statement"""

    _inherit = "statement.common"
    _name = "report.partner_statement.activity_statement"
    _description = "Partner Activity Statement"

    def _initial_balance_sql_q1(self, partners, date_start, account_type):
        return str(
            self._cr.mogrify(
                """
            SELECT l.partner_id, l.currency_id, l.company_id, l.id,
                (abs(COALESCE(l.balance, 0.0)) + sum(
                    coalesce(pr.pr_sign, 0.0) * coalesce(pr.amount, 0.0))
                ) * sign(COALESCE(l.balance, 0.0)) AS open_amount,
                (abs(COALESCE(l.amount_currency, 0.0)) + sum(
                    coalesce(pr.pr_sign, 0.0) * CASE
                        WHEN pr.currency_id IS NOT NULL AND pr.currency_id = l.currency_id
                        THEN coalesce(pr.amount_currency, 0.0)
                        WHEN cur.id IS NOT NULL AND ROUND(
                            abs(COALESCE(l.balance, 0.0)), cur.decimal_places) > 0.0
                        THEN ROUND(coalesce(pr.amount, 0.0) *
                                COALESCE(l.amount_currency, 0.0) / NULLIF(l.balance, 0.0),
                            cur.decimal_places)
                        ELSE ROUND(coalesce(pr.amount, 0.0) *
                            COALESCE((
                                SELECT r.rate FROM res_currency_rate r
                                JOIN account_move_line aml
                                    ON pr.credit_move_id = aml.id
                                WHERE r.currency_id = l.currency_id
                                    AND r.name <= aml.date
                                    AND (r.company_id IS NULL
                                        OR r.company_id = l.company_id)
                                ORDER BY r.company_id, r.name DESC LIMIT 1), 1.0),
                            cur.decimal_places)
                        END)
                ) * sign(COALESCE(l.amount_currency, 0.0)) AS open_amount_currency
            FROM (
                SELECT l.*, CASE
                    WHEN l.debit = 0.0 AND l.credit = 0.0 AND l.currency_id IS NOT NULL
                        AND ROUND(COALESCE(l.amount_currency, 0.0),
                            cur.decimal_places) > 0.0 THEN 1
                    WHEN l.debit = 0.0 AND l.credit = 0.0 AND l.currency_id IS NOT NULL
                        AND ROUND(COALESCE(l.amount_currency, 0.0),
                            cur.decimal_places) < 0.0 THEN -1
                    WHEN l.balance > 0.0 THEN 1 ELSE -1 END as sign
                FROM account_move_line l
                LEFT JOIN res_currency cur ON cur.id = l.currency_id
                ) l
            JOIN account_move m ON l.move_id = m.id
            LEFT JOIN res_currency cur ON cur.id = l.currency_id
            LEFT JOIN LATERAL (SELECT pr.*,
                CASE WHEN pr.credit_move_id = l.id THEN l.sign
                    ELSE -l.sign END AS pr_sign
                FROM account_partial_reconcile pr
                WHERE pr.max_date < %(date_start)s AND (
                    (pr.debit_move_id = l.id) OR (pr.credit_move_id = l.id))
            ) as pr ON TRUE
            WHERE l.partner_id IN %(partners)s
                AND l.account_internal_type = %(account_type)s
                AND (
                  (pr.id IS NOT NULL AND pr.max_date < %(date_start)s) OR
                  (pr.id IS NULL)
                ) AND l.date < %(date_start)s AND not l.blocked
                AND m.state IN ('posted')
            GROUP BY l.partner_id, l.currency_id, l.company_id,
                l.balance, l.amount_currency, l.id
        """,
                locals(),
            ),
            "utf-8",
        )

    def _initial_balance_sql_q2(self):
        return str(
            self._cr.mogrify(
                """
            SELECT Q1.partner_id, Q1.currency_id,
                sum(CASE WHEN Q1.currency_id is not null
                    THEN Q1.open_amount_currency
                    ELSE Q1.open_amount
                END) as balance, Q1.company_id
            FROM Q1
            GROUP BY Q1.partner_id, Q1.currency_id, Q1.company_id""",
                locals(),
            ),
            "utf-8",
        )

    def _initial_balance_sql_q3(self, company_id):
        return str(
            self._cr.mogrify(
                """
            SELECT Q2.partner_id, Q2.balance,
            COALESCE(Q2.currency_id, c.currency_id) AS currency_id
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            JOIN res_currency cur ON cur.id = COALESCE(Q2.currency_id, c.currency_id)
            WHERE c.id = %(company_id)s AND
                round(Q2.balance, cur.decimal_places) != 0.0
        """,
                locals(),
            ),
            "utf-8",
        )

    def _get_account_initial_balance(
        self, company_id, partner_ids, date_start, account_type
    ):
        balance_start = defaultdict(list)
        partners = tuple(partner_ids)
        # pylint: disable=E8103
        self.env.cr.execute(
            """WITH Q1 AS (%s),
                    Q2 AS (%s),
                    Q3 AS (%s)
        SELECT partner_id, currency_id, sum(balance) as balance
        FROM Q3
        GROUP BY partner_id, currency_id"""
            % (
                self._initial_balance_sql_q1(partners, date_start, account_type),
                self._initial_balance_sql_q2(),
                self._initial_balance_sql_q3(company_id),
            )
        )
        for row in self.env.cr.dictfetchall():
            balance_start[row.pop("partner_id")].append(row)
        return balance_start

    def _display_lines_sql_q1(self, partners, date_start, date_end, account_type):
        payment_ref = _("Payment")
        return str(
            self._cr.mogrify(
                """
            SELECT m.name AS move_id, l.partner_id, l.date,
                array_agg(l.id ORDER BY l.id) as ids,
                CASE WHEN (aj.type IN ('sale', 'purchase'))
                    THEN l.name
                    ELSE '/'
                END as name,
                CASE
                    WHEN (aj.type IN ('sale', 'purchase')) AND l.name IS NOT NULL
                        THEN l.ref
                    WHEN (aj.type in ('bank', 'cash'))
                        THEN %(payment_ref)s
                    ELSE m.ref
                END as case_ref,
                l.blocked, l.currency_id, l.company_id,
                sum(CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                    THEN l.amount_currency
                    ELSE l.debit
                END) as debit,
                sum(CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                    THEN l.amount_currency * (-1)
                    ELSE l.credit
                END) as credit,
                CASE WHEN l.date_maturity is null
                    THEN l.date
                    ELSE l.date_maturity
                END as date_maturity
            FROM account_move_line l
            JOIN account_move m ON (l.move_id = m.id)
            JOIN account_journal aj ON (l.journal_id = aj.id)
            WHERE l.partner_id IN %(partners)s
                AND l.account_internal_type = %(account_type)s
                AND %(date_start)s <= l.date
                AND l.date <= %(date_end)s
                AND m.state IN ('posted')
            GROUP BY l.partner_id, m.name, l.date, l.date_maturity,
                CASE WHEN (aj.type IN ('sale', 'purchase'))
                    THEN l.name
                    ELSE '/'
                END, case_ref, l.blocked, l.currency_id, l.company_id
        """,
                locals(),
            ),
            "utf-8",
        )

    def _display_lines_sql_q2(self, company_id):
        return str(
            self._cr.mogrify(
                """
            SELECT Q1.partner_id, Q1.move_id, Q1.date, Q1.date_maturity,
                Q1.name, Q1.case_ref as ref, Q1.debit, Q1.credit, Q1.ids,
                Q1.debit-Q1.credit as amount, Q1.blocked,
                COALESCE(Q1.currency_id, c.currency_id) AS currency_id
            FROM Q1
            JOIN res_company c ON (c.id = Q1.company_id)
            WHERE c.id = %(company_id)s
        """,
                locals(),
            ),
            "utf-8",
        )

    def _get_account_display_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)

        # pylint: disable=E8103
        self.env.cr.execute(
            """
        WITH Q1 AS (%s),
             Q2 AS (%s)
        SELECT partner_id, move_id, date, date_maturity, ids,
            COALESCE(name, '') as name, COALESCE(ref, '') as ref,
            debit, credit, amount, blocked, currency_id
        FROM Q2
        ORDER BY date, date_maturity, move_id"""
            % (
                self._display_lines_sql_q1(
                    partners, date_start, date_end, account_type
                ),
                self._display_lines_sql_q2(company_id),
            )
        )
        for row in self.env.cr.dictfetchall():
            res[row.pop("partner_id")].append(row)
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        if "company_id" not in data:
            wiz = self.env["activity.statement.wizard"].with_context(
                active_ids=docids, model="res.partner"
            )
            data.update(wiz.create({})._prepare_statement())
        data["amount_field"] = "amount"
        return super()._get_report_values(docids, data)
