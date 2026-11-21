Known limitations of the current implementation:

* Amounts are reported in the **company currency**, the currency carried by
  the analytic items themselves. Multi-currency invoices are prorated on their
  company-currency balance, so no exchange rate is applied a second time, but
  the report offers no per-currency breakdown.
* **Exchange differences and write-offs** generated at reconciliation time
  reach the report only through the settled amount they produce; they are not
  reported as their own rows.
* The proration divides by the invoice AP/AR total. An invoice whose AP/AR
  total is zero (fully discounted, or a technical entry) yields no cash rows
  rather than an error.
* Cash rows for direct expenses cover **bank and cash journals** only.
  Organisations that book petty cash through a miscellaneous journal will see
  those entries flagged ``No Cash Event``.
* The view is not materialised. On very large databases, filter by period or
  by analytic plan before opening the pivot without any grouping.
