.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
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

Define Accounts
---------------
There are three accounts associated to a bank account:
* Bank account view
* Bank Account. Matches the statement
* Bank Clearing Account. Is used for uncleared payments and receipts. The
  Bank Clearing Account is a reconcilable account.

In the definition of the bank account that is used to match with the bank
statement, define what will be the GL account used to record the uncleared
payments and receipts.

Define Account Journals
-----------------------
Create the following journals:
* Journal for Bank Statement reconciliation
* Journal to enter Payments and Receipts that have not yet cleared to the bank


Enter payments and receipts
---------------------------
Every time an invoice is paid, use the Journal to enter Payments and Receipts.
It will generate:
Dr. Accounts Payable
Cr. Bank Clearing Account

Create a bank statement
-----------------------
Create a bank statement and select the Journal defined for bank statement
reconciliation.

If you do not use a tool to integrate automatically the bank statement feed
into Odoo, you can press press the button “Import Payments and Receipts”
in order to add to the statements the payments and receipts that have been
generated, but that have not yet cleared the bank.

Use the “Reconcile” button to reconcile the entries in the bank statement
with the payments and receipts that have already cleared the bank.

If you chose to import the statement lines from uncleared payments and
receipts, this will be the moment where you will visually compare with the
online/paper bank statement, and reconcile the items that truly cleared the
bank.

The Odoo Bank Reconciliation Wizard will be used by the user to specifically
create the Bank Account entries by linking the Bank Statement lines with the
Bank Clearing Account items.

Dr. Bank Clearing Account
Cr. Bank Account

Once you have completed this process, some statement lines may be left
unreconciled (because they were truly not present in the online/physical
statement). In that case you can press the button “Remove Unreconciled”.

Print bank statement reconciliation summary
-------------------------------------------
It will report on the current balance of the Bank Account, and will show the
unreconciled entries of the Bank Clearing Account, classifying the them
between Outstanding Payments (that is, credits in the Bank Clearing Account)
and Outstanding Receipts (that is, debits in the Bank Clearing Account).

The application will also show the bank statement lines that have not yet
been reconciled yet, if any exists.

Once the user has fully processed the reconciliation with the bank clearing
account, all the entries in this bank clearing account should be reconciled,
and the bank account (used to match with the Statement) will truly
reflect the same information as the bank statement balance.

From a bank account perspective, the total amount held in the bank is the
sum of the balances of the bank clearing account (which should normally
show undeposited checks, for example) and the bank account used to match
with the statement.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/91/8.0


Known issues / Roadmap
======================

* For Odoo v9 there will be no need to use the clearing account.

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

To contribute to this module, please visit http://odoo-community.org.
