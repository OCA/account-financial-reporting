Journal Items Excel Export
==========================

This module extends the functionality of the journal items 
('account.move.line') list view and allow you to export the selected lines.

Installation
============

To install this module manually, you need also the **report_xls**
module located in:

https://launchpad.net/openerp-reporting-engines

Usage
=====

To use this module, you need to:

* go to the list view of the journal items
* select the line you wish to export
* click on the button on top to export

The Excel export can be tailored to your exact needs via the following methods
of the 'account.move.line' object:

*  **_report_xls_fields**

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

* **_report_xls_template**

  Change/extend the Excel template.

Credits
=======

Contributors
------------
* Noviat <info@noviat.com>
* Guillaume Auger <guillaume.auger@savoirfairelinux.com>

Maintainer
----------
.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
