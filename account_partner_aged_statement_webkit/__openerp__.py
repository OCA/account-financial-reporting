# -*- coding: utf-8 -*-
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
    'author': 'Savoir-faire Linux, '
              'Odoo Community Association (OCA)',
    'website': 'http://www.savoirfairelinux.com',
    'depends': [
        'report_webkit',
        'base_headers_webkit',
        'mail',
        'account',
    ],
    'license': 'AGPL-3',
    'category': 'Accounting',
    'description': """
Print & Send Partner Aged Statement by email
============================================

This module adds in the system :
 * a new mail template "Aged Statement Letter";
 * the ability to print the partner aged statement;
 * a button "Send by email" in the partner form view which load the template
 and attach the statement to the email.

Comparing to 'Overdue Payment' report provided with OpenERP, this one adds more
informations :
 * the summary per period
 * the list of invoices per period
 * the invoices are also shown with the foreign currency

 Both messages, in the PDF and the email are taken from the Overdue Payments
 Message defined on the Company's configuration.

Contributors
------------
* Marc Cassuto (marc.cassuto@savoirfairelinux.com)
* Vincent Vinet (vincent.vinet@savoirfairelinux.com)
    """,
    'data': [
        'partner_aged_statement_report.xml',
        'partner_aged_statement_view.xml',
        'partner_aged_statement_data.xml',
    ],
    'active': False,
    'installable': True
}
