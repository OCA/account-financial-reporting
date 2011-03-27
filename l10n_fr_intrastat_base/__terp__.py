# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (http://tiny.be). All Rights Reserved
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
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
    'name': 'Base module for Intrastat reporting (DEB + DES) for France',
    'version': '1.1',
    'category': 'Localisation/Report Intrastat',
    'license': 'AGPL-3',
    'description': """This module contains the common functions for 2 other modules :
- l10n_fr_intrastat_service : the module for the "Déclaration Européenne des Services" (DES)
- l10n_fr_intrastat_product : the module for the "Déclaration d'Echange de Biens" (DEB)
This module is not usefull if it's not used together with one of the other 2 modules.

WARNING : this module conflicts with the module "report_intrastat" from the addons. If you have already installed the module "report_intrastat", you should uninstall it first before installing this module.
    """,
    'author': 'Akretion and OpenERP S.A.',
    'website': 'http://www.akretion.com',
    'depends': ['account'],
    'init_xml': ['country_data.xml'],
    'update_xml': [
        'security/ir.model.access.csv',
        'product_view.xml',
        'country_view.xml',
        'report_intrastat_view.xml',
        'company_view.xml',
        'account_invoice_view.xml',
        'account_invoice_workflow.xml',
    ],
    'demo_xml': ['intrastat_demo.xml'],
    'installable': True,
    'active': False,
}
