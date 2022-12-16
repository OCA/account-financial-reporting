# Copyright 2022 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models

from .outstanding_statement import OutstandingStatement


class DetailedActivityStatement(models.AbstractModel):
    """Model of Detailed Activity Statement"""

    _inherit = "report.partner_statement.activity_statement"
    _name = "report.partner_statement.detailed_activity_statement"
    _description = "Partner Detailed Activity Statement"

    def _get_account_display_prior_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        return self._get_account_display_lines2(
            company_id, partner_ids, date_start, date_end, account_type
        )

    def _display_activity_reconciled_lines_sql_q1(self, sub):
        return str(
            self._cr.mogrify(
                f"""
            SELECT unnest(ids) as id
            FROM {sub}
        """,
                locals(),
            ),
            "utf-8",
        )

    def _display_activity_reconciled_lines_sql_q2(self, sub, date_end):
        return str(
            self._cr.mogrify(
                f"""
            SELECT l.id as rel_id, m.name AS move_id, l.partner_id, l.date, l.name,
                l.blocked, l.currency_id, l.company_id, {sub}.id,
            CASE WHEN l.ref IS NOT NULL
                THEN l.ref
                ELSE m.ref
            END as ref,
            CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                THEN avg(l.amount_currency)
                ELSE avg(l.debit)
            END as debit,
            CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                THEN avg(l.amount_currency * (-1))
                ELSE avg(l.credit)
            END as credit,
            CASE WHEN l.balance > 0.0
                THEN sum(coalesce(pc.amount, 0.0))
                ELSE -sum(coalesce(pd.amount, 0.0))
            END AS open_amount,
            CASE WHEN l.balance > 0.0
                THEN sum(coalesce(pc.debit_amount_currency, 0.0))
                ELSE -sum(coalesce(pd.credit_amount_currency, 0.0))
            END AS open_amount_currency,
            CASE WHEN l.date_maturity is null
                THEN l.date
                ELSE l.date_maturity
            END as date_maturity
            FROM {sub}
            LEFT JOIN account_partial_reconcile pd ON (
                pd.debit_move_id = {sub}.id AND pd.max_date <= %(date_end)s)
            LEFT JOIN account_partial_reconcile pc ON (
                pc.credit_move_id = {sub}.id AND pc.max_date <= %(date_end)s)
            LEFT JOIN account_move_line l ON (
                pd.credit_move_id = l.id OR pc.debit_move_id = l.id)
            LEFT JOIN account_move m ON (l.move_id = m.id)
            WHERE l.date <= %(date_end)s AND m.state IN ('posted')
            GROUP BY l.id, l.partner_id, m.name, l.date, l.date_maturity, l.name,
                CASE WHEN l.ref IS NOT NULL
                    THEN l.ref
                    ELSE m.ref
                END, {sub}.id,
                l.blocked, l.currency_id, l.balance, l.amount_currency, l.company_id
        """,
                locals(),
            ),
            "utf-8",
        )

    def _get_account_display_reconciled_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)

        # pylint: disable=E8103
        self.env.cr.execute(
            """
        WITH Q1 AS (%s),
             Q2 AS (%s),
             Q3 AS (%s),
             Q4 AS (%s),
             Q5 AS (%s),
             Q6 AS (%s)
        SELECT partner_id, currency_id, move_id, date, date_maturity, debit,
               credit, amount, open_amount, name, ref, blocked, id
        FROM Q6
        ORDER BY date, date_maturity, move_id"""
            % (
                self._display_activity_lines_sql_q1(
                    partners, date_start, date_end, account_type
                ),
                self._display_activity_lines_sql_q2("Q1", company_id),
                self._display_activity_reconciled_lines_sql_q1("Q2"),
                self._display_activity_reconciled_lines_sql_q2("Q3", date_end),
                self._display_outstanding_lines_sql_q2("Q4"),
                self._display_outstanding_lines_sql_q3("Q5", company_id),
            )
        )
        for row in self.env.cr.dictfetchall():
            res[row.pop("partner_id")].append(row)
        return res

    def _get_account_display_ending_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        return self._get_account_display_lines2(
            company_id, partner_ids, date_start, date_end, account_type
        )

    def _add_currency_prior_line(self, line, currency):
        return self._add_currency_line2(line, currency)

    def _add_currency_reconciled_line(self, line, currency):
        return self._add_currency_line2(line, currency)

    def _add_currency_ending_line(self, line, currency):
        return self._add_currency_line2(line, currency)


DetailedActivityStatement._get_account_display_lines2 = (
    OutstandingStatement._get_account_display_lines
)
DetailedActivityStatement._display_outstanding_lines_sql_q1 = (
    OutstandingStatement._display_outstanding_lines_sql_q1
)
DetailedActivityStatement._display_outstanding_lines_sql_q2 = (
    OutstandingStatement._display_outstanding_lines_sql_q2
)
DetailedActivityStatement._display_outstanding_lines_sql_q3 = (
    OutstandingStatement._display_outstanding_lines_sql_q3
)
DetailedActivityStatement._add_currency_line2 = OutstandingStatement._add_currency_line
