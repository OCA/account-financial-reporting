# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    'name': 'Account financial test data',
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Taktik, Odoo Community Association (OCA)",
    'category': 'Other',
    'depends': [
        "base",
        "account",
        "account_accountant",
        "l10n_fr",
    ],
    'demo': [],
    'data': [
        "data/settings_data.xml",
        "data/account_auto_installer.xml",
        "data/partners_data.xml",
    ],
    'installable': True,
}
