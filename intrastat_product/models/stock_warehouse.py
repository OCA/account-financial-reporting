# -*- coding: utf-8 -*-
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

from openerp import models, fields, api


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    region_id = fields.Many2one(
        'intrastat.region',
        string='Intrastat region')


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.multi
    def get_intrastat_region(self):
        self.ensure_one()
        locations = self.search(
            [('parent_left', '<=', self.parent_left),
             ('parent_right', '>=', self.parent_right)])
        warehouses = self.env['stock.warehouse'].search([
            ('lot_stock_id', 'in', [x.id for x in locations]),
            ('region_id', '!=', False)])
        if warehouses:
            return warehouses[0].region_id
        return None
