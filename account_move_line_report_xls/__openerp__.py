# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Account Move Line XLS export',
    'version': '0.6',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'description': """
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
    """,
    'depends': ['account', 'report_xls'],
    'data': [
        'report/move_line_list_xls.xml',
    ],
}
