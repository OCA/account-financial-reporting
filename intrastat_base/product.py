# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat base module for OpenERP
#    Copyright (C) 2010-2013 Akretion (http://www.akretion.com/)
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

from openerp.osv import osv, fields
from openerp.tools.translate import _

class product_template(osv.Model):
    _inherit = "product.template"
    _columns = {
        'exclude_from_intrastat': fields.boolean('Exclude from Intrastat reports', help="If set to True, the product or service will not be taken into account for Intrastat Product or Service reports. So you should leave this field to False unless you have a very good reason."),
        'is_accessory_cost' : fields.boolean('Is accessory cost', help='Activate this option for shipping costs, packaging costs and all services related to the sale of products. This option is used for Intrastat reports.'),
    }

    _defaults = {
        'exclude_from_intrastat': False,
    }


    def _check_accessory_cost(self, cr, uid, ids):
        for product in self.browse(cr, uid, ids):
            if product.is_accessory_cost and product.type != 'service':
                raise osv.except_osv(_('Error :'), _("The option 'Is accessory cost?' should only be activated on 'Service' products. You have activated this option for the product '%s' which is of type '%s'" % (product.name, product.type)))
        return True

    _constraints = [
        (_check_accessory_cost, "Error msg is in raise", ['is_accessory_cost', 'type'])
        ]

