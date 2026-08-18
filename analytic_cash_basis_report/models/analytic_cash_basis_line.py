# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from psycopg2.extensions import AsIs

from odoo import fields, models, tools

# Rules encoded in this view (validated against the golden dataset, see
# docs/PHASE1_RESULTS.md in the repository):
#   R1. Analytic lines sitting on payable/receivable accounts are manual
#       duplicates of the invoice analytic -> excluded everywhere.
#   R2. Analytic lines without a journal item (timesheets) -> excluded.
#   R3. Cash amounts derive from account_partial_reconcile, prorating each
#       invoice's analytic lines by settled_amount / invoice AP-AR total.
#   R4. Direct bank/cash-journal expenses: move date is the cash date.
#   R5. Misc-journal lines with no cash event are bucketed 'no_cash_event'.
VIEW_SQL = """
WITH base_line AS (
    SELECT aal.id AS analytic_line_id,
           aml.account_id,
           aal.account_id AS analytic_account_id,
           aaa.plan_id,
           aal.date AS accrual_date,
           aal.amount,
           aml.move_id,
           am.move_type,
           am.partner_id,
           am.company_id,
           rc.currency_id,
           aj.type AS journal_type,
           CASE
               WHEN am.move_type IN ('out_invoice', 'out_refund')
                    THEN 'revenue'
               WHEN am.move_type IN ('in_invoice', 'in_refund')
                    THEN 'cost'
               WHEN aal.amount > 0 THEN 'revenue'
               ELSE 'cost'
           END AS kind
    FROM account_analytic_line aal
    JOIN account_analytic_account aaa ON aaa.id = aal.account_id
    JOIN account_move_line aml ON aml.id = aal.move_line_id
    JOIN account_account aa ON aa.id = aml.account_id
    JOIN account_move am ON am.id = aml.move_id
    JOIN account_journal aj ON aj.id = am.journal_id
    JOIN res_company rc ON rc.id = am.company_id
    WHERE aa.account_type NOT IN ('liability_payable', 'asset_receivable')
      AND am.state = 'posted'
),
invoice_total AS (
    SELECT aml.move_id,
           SUM(ABS(aml.balance)) AS payable_total
    FROM account_move_line aml
    JOIN account_account aa ON aa.id = aml.account_id
    WHERE aa.account_type IN ('liability_payable', 'asset_receivable')
      AND aml.parent_state = 'posted'
    GROUP BY aml.move_id
),
settlement AS (
    SELECT aml_inv.move_id AS invoice_move_id,
           apr.id AS partial_id,
           apr.amount AS paid_amount,
           am_pay.date AS payment_date
    FROM account_partial_reconcile apr
    JOIN account_move_line aml_inv
         ON aml_inv.id IN (apr.debit_move_id, apr.credit_move_id)
    JOIN account_move am_inv ON am_inv.id = aml_inv.move_id
    JOIN account_move_line aml_pay
         ON aml_pay.id = CASE WHEN aml_inv.id = apr.debit_move_id
                              THEN apr.credit_move_id
                              ELSE apr.debit_move_id END
    JOIN account_move am_pay ON am_pay.id = aml_pay.move_id
    WHERE am_inv.move_type IN ('in_invoice', 'in_refund',
                               'out_invoice', 'out_refund')
      AND am_inv.id <> am_pay.id
)
-- Ids MUST be deterministic: the web client reads rows by id in a query
-- separate from the search; row_number() OVER () re-numbers rows on every
-- execution and made ids point at different records between the two
-- queries (wrong rows under groups, cross-company access errors).
-- Encoding: id = key * 10 + branch, branch 1=accrual, 2=settlement,
-- 3=direct; settlement key pairs (analytic line, partial reconcile).
SELECT u.*
FROM (
    -- Accrual rows: every real analytic line once, at its accrual date.
    SELECT (b.analytic_line_id::bigint * 10 + 1) AS id,
           b.analytic_line_id,
           b.account_id,
           b.analytic_account_id,
           b.plan_id,
           b.company_id,
           b.currency_id,
           b.partner_id,
           b.move_id,
           b.accrual_date AS date,
           'accrual' AS regime,
           b.amount,
           CASE
               WHEN b.move_type IN ('in_invoice', 'in_refund',
                                    'out_invoice', 'out_refund')
                    THEN 'invoice'
               WHEN b.journal_type IN ('bank', 'cash') THEN 'direct'
               ELSE 'no_cash_event'
           END AS bucket,
           b.kind
    FROM base_line b

    UNION ALL
    -- Cash rows for invoices: prorated per settlement, at payment date.
    SELECT ((b.analytic_line_id::bigint * 10000000 + s.partial_id) * 10 + 2)
               AS id,
           b.analytic_line_id,
           b.account_id,
           b.analytic_account_id,
           b.plan_id,
           b.company_id,
           b.currency_id,
           b.partner_id,
           b.move_id,
           s.payment_date AS date,
           'cash' AS regime,
           ROUND((b.amount * s.paid_amount
                  / NULLIF(it.payable_total, 0))::numeric, 2) AS amount,
           'settlement' AS bucket,
           b.kind
    FROM base_line b
    JOIN invoice_total it ON it.move_id = b.move_id
    JOIN settlement s ON s.invoice_move_id = b.move_id
    WHERE b.move_type IN ('in_invoice', 'in_refund',
                          'out_invoice', 'out_refund')

    UNION ALL
    -- Cash rows for direct bank/cash expenses: move date, ratio 1.
    SELECT (b.analytic_line_id::bigint * 10 + 3) AS id,
           b.analytic_line_id,
           b.account_id,
           b.analytic_account_id,
           b.plan_id,
           b.company_id,
           b.currency_id,
           b.partner_id,
           b.move_id,
           b.accrual_date AS date,
           'cash' AS regime,
           b.amount,
           'direct' AS bucket,
           b.kind
    FROM base_line b
    WHERE b.move_type = 'entry'
      AND b.journal_type IN ('bank', 'cash')
) u
"""


class AnalyticCashBasisLine(models.Model):
    _name = "analytic.cash.basis.line"
    _description = "Analytic Cash Basis vs Accrual Line"
    _auto = False
    _order = "date desc, id desc"

    analytic_line_id = fields.Many2one(
        "account.analytic.line", string="Analytic Line", readonly=True
    )
    account_id = fields.Many2one(
        "account.account", string="Financial Account", readonly=True
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Analytic Account", readonly=True
    )
    plan_id = fields.Many2one(
        "account.analytic.plan", string="Analytic Plan", readonly=True
    )
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    move_id = fields.Many2one("account.move", string="Journal Entry", readonly=True)
    date = fields.Date(readonly=True)
    regime = fields.Selection(
        [("accrual", "Accrual"), ("cash", "Cash")],
        readonly=True,
    )
    amount = fields.Monetary(readonly=True)
    kind = fields.Selection(
        [("cost", "Costs"), ("revenue", "Revenue")],
        string="Nature",
        readonly=True,
    )
    bucket = fields.Selection(
        [
            ("invoice", "Invoice"),
            ("settlement", "Payment of Invoice"),
            ("direct", "Direct Bank/Cash"),
            ("no_cash_event", "No Cash Event"),
        ],
        string="Source",
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            "CREATE OR REPLACE VIEW %s AS (%s)",
            (AsIs(self._table), AsIs(VIEW_SQL)),
        )
