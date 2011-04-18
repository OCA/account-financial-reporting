# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for OpenERP
#    Copyright (C) 2010-2011 Akretion (http://www.akretion.com/) All Rights Reserved
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

from osv import osv, fields

# We want to have the country field on res_partner_address always set
# because the selection of invoices for intrastat reports is based
# on the country of the invoice partner address !
class res_partner_address(osv.osv):
    _inherit = 'res.partner.address'
    _columns = {
       'country_id': fields.many2one('res.country', 'Country', required=True),
     }

res_partner_address()

