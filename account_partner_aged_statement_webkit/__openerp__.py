# -*- encoding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Partner Aged Statement',
    "version": "1.0",
    'author': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'depends': [
        'account_financial_report_webkit_xls',
        'report_webkit',
        'base_headers_webkit',
        'mail',
    ],
    'category': 'Accounting',
    'description': """
Print & Send Partner Aged Statement by email
============================================

This module adds in the system :
 * a new mail template "Aged Statement Letter";
 * the abitlity to print the partner aged statement;
 * a button "Send by email" in the pricelist form view which load the template
 and attache the pricelist to the email.

So far the module does not drill down through pricelist items that are
based on another pricelist or based on purchase pricelists.

Contributors
------------
* Marc Cassuto (marc.cassuto@savoirfairelinux.com)
    """,
    'data': [
        'partner_aged_statement_report.xml',
        'partner_aged_statement_view.xml',
        'partner_aged_statement_data.xml',
    ],
    'active': False,
    'installable': True
}
