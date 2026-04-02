This module adds a set of financial reports. They are accessible under
Invoicing / Reporting / OCA accounting reports.

- General ledger
- Trial Balance
- Open Items
- Aged Partner Balance
- VAT Report
- Journal Ledger

Currently General ledger, Trial Balance and Open Items are fully
compatible with a foreign currency set up in account in order to display
balances. Moreover, any foreign currency used in account move lines is
properly shown.

In case that in an account has not been configured a second currency
foreign currency balances are not available.

Invoicing / Settings / Invoicing / OCA Aged Report Configuration you will be able to set
dynamic intervals that will appear on the Aged Partner Balance.
For further information, check CONFIGURE.rst

**Analytic Distribution column**

The following reports support an optional *Analytic Distribution* column
(enabled by default via a wizard checkbox) that shows the analytic accounts
and their split percentages for each journal item:

- General Ledger (controlled by *Show Analytic Account*)
- Journal Ledger (*Show Analytic Distribution*)
- Open Items (*Show Analytic Distribution*)
- Aged Partner Balance (*Show Analytic Distribution*, only when
  *Show Move Line Details* is enabled)

The column is available in both PDF and XLSX exports.
