# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat Product module for Odoo
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
    'name': 'Intrastat Product',
    'version': '8.0.1.4.1',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Base module for Intrastat Product',
    'author': 'Akretion, Noviat, Odoo Community Association (OCA)',
    'depends': [
        'intrastat_base',
        'product_harmonized_system',
        'stock_picking_invoice_link',
        'sale_stock',
        'purchase',
        ],
    'conflicts': ['report_intrastat'],
    'data': [
        'views/hs_code.xml',
        'views/intrastat_region.xml',
        'views/intrastat_unit.xml',
        'views/intrastat_transaction.xml',
        'views/intrastat_transport_mode.xml',
        'views/intrastat_product_declaration.xml',
        'views/res_company.xml',
        'views/account_invoice.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
        'security/intrastat_security.xml',
        'security/ir.model.access.csv',
        'data/intrastat_transport_mode.xml',
        'data/intrastat_unit.xml',
    ],
    'demo': ['demo/intrastat_demo.xml'],
    'installable': True,
}
