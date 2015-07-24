# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Joel Grand-Guillaume and Vincent Renaville
#    Copyright 2013 Camptocamp SA
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
    'name': 'Account Export CSV',
    'version': '1.1',
    'depends': [
        'account',
    ],
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'description': """

    Add a wizard that allow you to export a csv file based on accounting
    journal entries

    - Trial Balance
    - Analytic Balance (with accounts)
    - Journal Entries

    You can filter by period

    TODO: rearange wizard view with only one button to generate file plus
    define a selection list to select report type
    """,
    'website': 'http://www.camptocamp.com',
    'data': [
        'wizard/account_export_csv_view.xml',
        'menu.xml',
    ],
    'installable': True,
    'active': False,
}
