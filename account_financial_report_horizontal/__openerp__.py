# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2012 Therp BV (<http://therp.nl>),
#    Copyright (C) 2013 Agile Business Group sagl
#    (<http://www.agilebg.com>) (<lorenzo.battistini@agilebg.com>)
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
    "name": "Accounting Financial Reports Horizontal",
    "version": "8.0.0.3.0",
    "author": "Therp BV,Agile Business Group,Odoo Community Association (OCA)",
    "category": 'Accounting & Finance',
    'website': 'https://github.com/OCA/account-financial-reporting',
    'license': 'AGPL-3',
    "depends": ["account"],
    'data': [
        "data/report_paperformat.xml",
        "data/ir_actions_report_xml.xml",
        "report/report_financial.xml",
    ],
    'demo': [],
    'test': [],
    'active': False,
}
