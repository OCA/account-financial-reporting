# -*- coding: utf-8 -*-
##############################################################################
#
#    Intrastat base module for Odoo
#    Copyright (C) 2010-2014 Akretion (http://www.akretion.com/)
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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_accessory_cost = fields.Boolean(
        string='Is accessory cost',
        help="Activate this option for shipping costs, packaging "
        "costs and all services related to the sale of products. "
        "This option is used for Intrastat reports.")

    @api.multi
    @api.constrains('type', 'is_accessory_cost')
    def _check_accessory_cost(self):
        for this in self:
            if this.is_accessory_cost and this.type != 'service':
                raise ValidationError(
                    _("The option 'Is accessory cost?' should only be "
                        "activated on 'Service' products. You have activated "
                        "this option for the product '%s' which is of type "
                        "'%s'") %
                    (this.name, this.type))
