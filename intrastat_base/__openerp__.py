# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for Odoo
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
    'category': 'Localisation/Report Intrastat',
    'license': 'AGPL-3',
    'summary': 'Base module for Intrastat reporting',
    'description': """This module contains the common functions for 2 other modules :
- l10n_fr_intrastat_service : the module for the "Déclaration Européenne des Services" (DES)
- l10n_fr_intrastat_product : the module for the "Déclaration d'Echange de Biens" (DEB)
This module is not usefull if it's not used together with one of those 2 modules or other country-specific intrastat modules.

This module doesn't have any France-specific stuff. So it can be used as a basis for other intrastat modules for other EU countries.

WARNING : this module conflicts with the module "report_intrastat" from the addons. If you have already installed the module "report_intrastat", you should uninstall it first before installing this module.

Please contact Alexis de Lattre from Akretion <alexis.delattre@akretion.com> for any help or question about this module.
    """,
    'author': 'Akretion',
    'website': 'http://www.akretion.com',
    'depends': ['base_vat'],
    'data': [
        'country_data.xml',
        'product_view.xml',
        'partner_view.xml',
        'country_view.xml',
        'tax_view.xml',
        'company_view.xml',
        'intrastat_menu.xml',
    ],
    'demo': ['intrastat_demo.xml'],
    'installable': True,
}
