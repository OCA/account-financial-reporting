# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
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
    'name': 'Intrastat Product Declaration for Belgium',
    'version': '0.1',
    'category': 'Intrastat',
    'license': 'AGPL-3',
    'summary': 'Base module for Intrastat Product',
    'author': 'Noviat, Odoo Community Association (OCA)',
    'depends': [
        'intrastat_product',
        'l10n_be_partner',
        ],
    'conflicts': [
        'l10n_be_intrastat',
        'report_intrastat',
        ],
    'data': [
        'security/intrastat_security.xml',
        'security/ir.model.access.csv',
        'data/intrastat_region.xml',
        'data/intrastat_transaction.xml',
        'views/intrastat_region.xml',
        'views/res_company.xml',
        'views/stock_warehouse.xml',
        'views/intrastat_installer.xml',
        'views/l10n_be_intrastat_product.xml',
    ],
    'installable': True,
}
