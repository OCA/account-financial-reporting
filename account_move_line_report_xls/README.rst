Journal Items Excel Export
==========================

This module adds a button on the journal items ('account.move.line') list view
in order to export the selected lines.

If you are installing this module manually, you need also the **report_xls**
module located in:
https://launchpad.net/openerp-reporting-engines

Report customisation
''''''''''''''''''''

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

Customisation assistance
''''''''''''''''''''''''
Contact info@noviat.com for help with the customisation and/or development
of Excel reports in OpenERP.

