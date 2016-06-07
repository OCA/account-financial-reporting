WITH view_q as (
  SELECT
    ml.date,
    acc.id AS account_id,
    ml.debit,
    ml.credit,
    ml.name AS name,
    ml.ref,
    ml.journal_id,
    ml.partner_id,
    SUM(debit - credit) OVER w_account - (debit - credit) AS init_balance,
    SUM(debit - credit) OVER w_account AS cumul_balance
  FROM account_account AS acc
    LEFT JOIN account_move_line AS ml ON (ml.account_id = acc.id)
    INNER JOIN account_move AS m ON (ml.move_id = m.id)
    INNER JOIN account_account_type aat ON (acc.user_type_id = aat.id)
  WHERE ml.date >= %(fy_date)s OR aat.include_initial_balance IS TRUE
  WINDOW w_account AS (
    PARTITION BY acc.code
    ORDER BY ml.date, ml.id
  )
  ORDER BY acc.id, ml.date
)
INSERT INTO ledger_report_wizard_line (
  date,
  name,
  journal_id,
  account_id,
  partner_id,
  ref,
  label,
  --counterpart
  init_balance,
  debit,
  credit,
  cumul_balance,
  wizard_id
)
SELECT
  date,
  name,
  journal_id,
  account_id,
  partner_id,
  ref,
  ' TODO label ' AS label,
  --counterpart
  init_balance,
  debit,
  credit,
  cumul_balance,
  %(wizard_id)s AS wizard_id
FROM view_q
WHERE date BETWEEN %(date_from)s AND %(date_to)s;
