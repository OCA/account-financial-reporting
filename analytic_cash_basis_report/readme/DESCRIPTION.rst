Odoo reports analytic amounts on an **accrual basis** only: an analytic item
is dated at its journal entry date and carries the full amount, whether the
invoice was paid or not. For organisations that steer by cash -- associations,
cooperatives, project-driven service companies, and anyone whose customers pay
in installments -- that view answers the wrong question.

This module adds a read-only report that shows the same analytic amounts under
**both regimes side by side**, per analytic account and per period:

* **Accrual**: the analytic item at its entry date, full amount. This is what
  Odoo already reports natively, minus the duplicate sources described below.
* **Cash**: the same analytic amount split across each payment installment and
  dated at the payment date, derived from the reconciliations
  (``account.partial.reconcile``).

Worked example
~~~~~~~~~~~~~~

A vendor bill of 3,000 is split 50/50 between two analytic accounts and paid
in three installments of 1,000, in March, April and May.

============ ================== ================== ==================
Regime       March              April              May
============ ================== ================== ==================
Accrual      1,500 per account  --                 --
Cash         500 per account    500 per account    500 per account
============ ================== ================== ==================

The accrual line stays whole in the invoice month; the cash lines follow the
money, keeping the 50/50 analytic split of the original bill.

Rules applied
~~~~~~~~~~~~~

The report is a SQL view. Five rules keep it explainable:

#. Analytic items placed on **payable/receivable accounts** are treated as
   manual duplicates of the invoice analytic and are excluded from both
   regimes. Placing analytic items on the AP/AR line is a common workaround
   for the missing cash view; counting them here would double every amount.
#. Analytic items **with no journal item** (timesheets, for instance) are
   excluded: they carry no accounting amount to settle.
#. Cash amounts for invoices are **prorated per settlement**:
   ``analytic_amount * settled_amount / invoice AP-AR total``, dated at the
   payment entry date. Partial payments, over-payments and credit notes are
   all handled by the same proration.
#. Expenses booked **directly in a bank or cash journal** (no invoice) count
   as cash on the entry date, with no proration.
#. Miscellaneous entries with **no cash event at all** are kept in the accrual
   regime and flagged ``No Cash Event``, so the two regimes remain
   reconcilable instead of silently diverging.

This module does not touch the cash-basis **tax** mechanism of Odoo
(``account.tax.cash.basis``), and it does not create journal entries. It is a
reporting view over data that already exists.
