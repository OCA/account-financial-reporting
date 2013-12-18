# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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
##############################################################################

{
    'name': 'Account Move Line XLS export',
    'version': '0.5',
    'license': 'AGPL-3',
    'author': 'Noviat',
    'category' : 'Accounting & Finance',
    'description': """

Journal Items Excel Export
==========================

This module adds a button on the journal items ('account.move.line') list view in order to export the selected lines.

If you are installing this module manually, you need also the module 'report_xls', that is located in:
https://launchpad.net/openerp-reporting-engines"

    """,
    'depends': ['account', 'report_xls'],
    'demo_xml': [],
    'init_xml': [],
    'update_xml' : [
        'report/move_line_list_xls.xml',      
    ],
}
