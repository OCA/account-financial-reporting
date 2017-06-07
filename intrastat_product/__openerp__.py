# -*- encoding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
#    Copyright (C) 2011-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2015 Noviat (http://www.noviat.com)
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
    'name': 'Intrastat Product',
    'version': '1.3',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Base module for Intrastat Product',
    'author': 'Akretion, Noviat, Odoo Community Association (OCA)',
    'depends': [
        'intrastat_base',
        'product_harmonized_system',
        'stock',
        ],
    'conflicts': ['report_intrastat'],
    'data': [
        'intrastat_view.xml',
        'intrastat_declaration_view.xml',
        'res_company_view.xml',
        'account_invoice_view.xml',
        'stock_view.xml',
        'security/intrastat_security.xml',
        'security/ir.model.access.csv',
        'data/intrastat_transport_mode.xml',
        'data/intrastat_unit.xml',
    ],
    'demo': ['intrastat_demo.xml'],
    'installable': True,
}
