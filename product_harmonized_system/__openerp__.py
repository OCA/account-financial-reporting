# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2009-2015 Noviat (http://www.noviat.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Luc de Meyer <info@noviat.com>
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
    'name': 'Product Harmonized System Codes',
    'version': '8.0.0.2.0',
    'category': 'Reporting',
    'license': 'AGPL-3',
    'summary': 'Base module for Product Import/Export reports',
    'author': 'Akretion, Noviat, Odoo Community Association (OCA)',
    'depends': ['product'],
    'conflicts': ['report_intrastat'],
    'data': [
        'security/product_hs_security.xml',
        'security/ir.model.access.csv',
        'views/hs_code.xml',
        'views/product_category.xml',
        'views/product_template.xml',
    ],
    'demo': [
        'demo/product_demo.xml',
    ],
    'installable': True,
}
