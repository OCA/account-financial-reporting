.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================================
Bank Statement Reconciliation Summary
=====================================

The Bank Reconciliation Summary shows how your actual bank statement balance
and the balance of the bank account in Odoo match, after taking into account
any unreconciled items.

This report is useful if your bank account's statement balance and balance
in Odoo do not match, and you need to check for duplicate or manually created
transactions that might cause the discrepancy.

This report was created, inspired by Xero’s bank reconciliation summary,
https://help.xero.com/Report_BankRec, and from a basic explanation of the
bank statement reconciliation summary:
http://www.accountingcoach.com/bank-reconciliation/explanation.


Usage
=====

#. Go to *Accounting / Reports / OCA accounting reports / Bank Statement Reconciliation*
#. Enter the end date for your analysis, the bank journal and the actual bank
   balance at that date.

The report displays the following sections:

* Balance in Odoo
* Plus Outstanding Payments - payments in odoo not yet reconciled
* Less Outstanding Receipts - payments in odoo not yet reconciled
* Plus Un-Reconciled Statement Lines - statement lines not yet reconciled
* Statement Balance

If the theoretical Statement Balance does not match with Odoo, it will
display the Computed (theoretical) balance, the Actual Balance and
the Unencoded Statement Amount.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/10.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-reporting/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-reporting/issues/new?body=module:%20account_tax_report_no_zeroes%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Jordi Ballester Alomar <contact@eficent.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
