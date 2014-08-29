Differences with account_financial_report_webkit Trial Balance
==============================================================

This module is complementary to the 'account_financial_report_webkit'/'account_financial_report_webkit_xls' modules Trial Balance.

Main differences:

1) Main purpose of the report
-----------------------------

The main purpose of this report is to have a 'single click' view on the operational performance.
If you select the top level P&L accounts and the periods, you get the P&L details as well as the summed up P&L results.

2) Report by period
-------------------

The financial performance for the selected set of accounts is reported by fiscal period.
In the last column the results of the fiscal periods are totalised.
These totals are equal to the 'account_financial_report_webkit' totals (if opening entries are present, cf. infra).

3) Initial Balance
------------------

This report collects his data via a query on the accounting entries per period.
As a consequence, there is no 'Initial Balance' logic such as implemented in the 'account_financial_report_webkit' module.
In order to include the 'Initial Balance' data in this report, you should first generate the opening entries for the selected fiscal year and include the Opening Period into the selected period range.
By default the Opening & Close periods are excluded.

4) Reporting Level
------------------

The report wizard allows to select a reporting level. 
This level corresponds to the depth in the Chart of Accounts. 
You can e.g. select level 1 to report only on the top level accounts (the general account classes).

   