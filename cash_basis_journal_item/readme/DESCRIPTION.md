This module provides a dedicated model (``cash.basis.move.line``) that stores
cash basis journal items generated from posted journal entries. It recognizes
revenue and expense on a cash basis using two sources:

1. **Direct copy** -- Journal items from cash basis journals (bank, cash,
   general) are copied directly at 100%.
2. **Proportional recognition** -- When invoices are partially or fully paid,
   the corresponding journal items are recognized proportionally based on the
   reconciled amount.

A scheduled action (cron) processes new posted moves and partial reconciliations
automatically, handling rounding adjustments to ensure balanced entries.
