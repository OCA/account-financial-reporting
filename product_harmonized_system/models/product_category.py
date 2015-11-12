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

from openerp import models, fields, api


class ProductCategory(models.Model):
    _inherit = "product.category"

    hs_code_id = fields.Many2one(
        'hs.code', string='H.S. Code',
        company_dependent=True, ondelete='restrict',
        help="Harmonised System Code. If this code is not "
        "set on the product itself, it will be read here, on the "
        "related product category.")

    @api.multi
    def get_hs_code_recursively(self):
        self.ensure_one()
        if self.hs_code_id:
            res = self.hs_code_id
        elif self.parent_id:
            res = self.parent_id.get_hs_code_recursively()
        else:
            res = None
        return res
