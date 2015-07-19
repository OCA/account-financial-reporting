# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat base module for Odoo
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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
    'name': 'Intrastat Reporting Base',
    'version': '1.1',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Base module for Intrastat reporting',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.akretion.com',
    'depends': ['base_vat'],
    'conflicts': ['report_intrastat'],
    'data': [
        'country_data.xml',
        'product_view.xml',
        'partner_view.xml',
        'country_view.xml',
        'tax_view.xml',
        'company_view.xml',
        'intrastat_view.xml',
    ],
    'demo': ['intrastat_demo.xml'],
    'installable': True,
}
