Go to *Accounting > Reporting > Analytic: Cash vs Accrual*.

The report opens as a pivot grouped by analytic account (rows) and month x
regime (columns), so both regimes read side by side. A list view and a graph
view are available from the view switcher.

Useful moves:

* **Focus on one regime**: the *Accrual* and *Cash* filters in the search
  panel.
* **Compare projects or departments**: group by *Analytic Plan*.
* **Audit a difference**: switch to the list view and add the *Source* column.
  It tells you where each row came from -- ``Invoice``, ``Payment of
  Invoice``, ``Direct Bank/Cash`` or ``No Cash Event``.
* **Find entries that will never turn into cash**: the *No Cash Event* filter
  isolates miscellaneous entries with no settlement, which is usually where an
  unexplained gap between the two regimes lives.
* **Export**: the standard pivot download button produces an XLSX.

Reading the amounts
~~~~~~~~~~~~~~~~~~~

Amounts keep the sign convention of the analytic items: costs are negative and
revenue is positive. The *Nature* field (``Costs`` / ``Revenue``) is derived
from the move type, so you can split the pivot by it instead of relying on the
sign.

The sum of the cash rows of an invoice equals the accrual row only once the
invoice is fully paid. A partially paid invoice shows the full amount under
accrual and only the settled share under cash -- which is the point of the
report.

Read access is granted to *Billing* and *Billing Readonly* users. The report
is restricted per company by a record rule, so multi-company users only see
the companies they have active.
