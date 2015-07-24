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
    'name': 'Financial Journal reports',
    'version': '0.2',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'description': """

Journal Reports
===============

This module adds journal reports by period and by fiscal year with
    - entries printed per move
    - option to group entries with same general account & VAT case
    - vat info per entry
    - vat summary

These reports are available in PDF and XLS format.

This module depends upon the 'report_xls' module,
cf. https://launchpad.net/openerp-reporting-engines

    """,
    'depends': [
        'account_voucher',
        'report_xls',
    ],
    'demo': [],
    'data': [
        'wizard/print_journal_wizard.xml',
    ],
}
