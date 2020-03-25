.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==========================
Journal Items Excel Export
==========================

This module extends the functionality of the journal items 
('account.move.line') list view and allow you to export the selected lines.

Installation
============

To install this module, you need also the **report_xlsx_helper**
module located in:

https://github.com/OCA/reporting-engine

Usage
=====

To use this module, you need to:

* go to the list view of the journal items
* select the lines you wish to export
* click on the button on top to export

The Excel export can be tailored to your exact needs via the following methods
of the 'account.move.line' object:

*  **_report_xlsx_fields**

   Add/drop columns or change order from the list of columns that are defined
   in the Excel template.

   The following fields are defined in the Excel template:

     move, name, date, journal, period, partner, account,
     date_maturity, debit, credit, balance,
     reconcile, reconcile_partial, analytic_account,
     ref, partner_ref, tax_code, tax_amount, amount_residual,
     amount_currency, currency_name, company_currency,
     amount_residual_currency, product, product_ref', product_uom, quantity,
     statement, invoice, narration, blocked

* **_report_xlsx_template**

  Change/extend the Excel template.
