# Copyright 2023 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountAccount(models.Model):
    _inherit = "account.account"

    def _get_open_items_at_date(self, date, only_posted_moves):
        if not date or not self:
            return []
        move_states = ["posted"]
        if not only_posted_moves:
            move_states.append(["draft"])
        query = """
        SELECT
        L.ID AS LINE_ID,
        L.date_maturity AS date_maturity,
        L.date AS date,
        L.NAME AS LINE_NAME,
        M.NAME AS MOVE_NAME,
        AA.ID AS ACCOUNT_ID,
        AA.NAME AS ACCOUNT_NAME,
        CASE
            WHEN (
                L.CURRENCY_ID IS NOT NULL
                AND L.AMOUNT_CURRENCY > 0.0
            )
            THEN AVG(L.AMOUNT_CURRENCY)
            ELSE AVG(L.DEBIT)
            END AS DEBIT,
            CASE
                WHEN (
                    L.CURRENCY_ID IS NOT NULL
                    AND L.AMOUNT_CURRENCY < 0.0
                )
                THEN AVG(L.AMOUNT_CURRENCY * (-1))
                ELSE AVG(L.CREDIT)
            END AS CREDIT,
            CASE
                WHEN L.BALANCE > 0.0 THEN L.BALANCE - SUM(COALESCE(PD.AMOUNT, 0.0))
                ELSE L.BALANCE + SUM(COALESCE(PC.AMOUNT, 0.0))
            END AS OPEN_AMOUNT,
            CASE
                WHEN L.BALANCE > 0.0 THEN L.AMOUNT_CURRENCY -
                SUM(COALESCE(PD.DEBIT_AMOUNT_CURRENCY, 0.0))
                ELSE L.AMOUNT_CURRENCY + SUM(COALESCE(PC.CREDIT_AMOUNT_CURRENCY, 0.0))
            END AS OPEN_AMOUNT_CURRENCY,
            CASE
                WHEN L.DATE_MATURITY IS NULL THEN L.DATE
                ELSE L.DATE_MATURITY
            END AS DATE_MATURITY
        FROM
            ACCOUNT_MOVE_LINE L
            JOIN ACCOUNT_ACCOUNT AA ON (AA.ID = L.ACCOUNT_ID)
            JOIN ACCOUNT_MOVE M ON (L.MOVE_ID = M.ID)
            LEFT JOIN (
                SELECT
                PR.*
                FROM
                ACCOUNT_PARTIAL_RECONCILE PR
                INNER JOIN ACCOUNT_MOVE_LINE L2 ON PR.CREDIT_MOVE_ID = L2.ID
                WHERE
                    L2.DATE <= %(date)s
                    ) AS PD ON PD.DEBIT_MOVE_ID = L.ID
                LEFT JOIN (
                    SELECT
                    PR.*
                    FROM
                    ACCOUNT_PARTIAL_RECONCILE PR
                    INNER JOIN ACCOUNT_MOVE_LINE L2 ON PR.DEBIT_MOVE_ID = L2.ID
                    WHERE
                    L2.DATE <= %(date)s
            ) AS PC ON PC.CREDIT_MOVE_ID = L.ID
        WHERE
            (
                (
                    PD.ID IS NOT NULL
                    AND PD.MAX_DATE <= %(date)s
                    OR (
                        PC.ID IS NOT NULL
                        AND PC.MAX_DATE <= %(date)s
                        OR (
                            PD.ID IS NULL
                            AND PC.ID IS NULL
                        )
                    )
                    AND L.DATE <= %(date)s
                    AND M.STATE IN %(move_state)s
                )
            )
        AND AA.RECONCILE = TRUE
        AND aa.id IN %(aa_ids)s
        GROUP BY
            L.ID,
            M.NAME,
            AA.ID,
            AA.NAME
        """
        self.env.cr.execute(
            query,
            {"date": date, "aa_ids": tuple(self.ids), "move_state": tuple(move_states)},
        )
        return self.env.cr.dictfetchall()
